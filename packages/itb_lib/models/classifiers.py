from typing import List, Tuple

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import lightgbm as lgbm
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

#
# GB
#


def train_predict_gb(
    df_X: pd.DataFrame, df_y: pd.Series, df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Train model with the specified hyper-parameters and return its predictions for the test data.
    """
    model_pair = train_gb(df_X, df_y, model_config)
    y_test_hat = predict_gb(model_pair, df_X_test, model_config)
    return y_test_hat


def train_gb(
    df_X: pd.DataFrame, df_y: pd.Series, model_config: dict
) -> Tuple[lgbm.Booster, StandardScaler]:
    """
    Train a LightGBM model with the specified hyper-parameters and return the model (and scaler if any).
    """
    # Double column set if required
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        max_shift = max(shifts)
        df_X = double_columns(df_X, shifts)
        df_X = df_X.iloc[max_shift:]
        df_y = df_y.iloc[max_shift:]

    # Scale
    is_scale = model_config.get("train", {}).get("is_scale", False)
    if is_scale:
        scaler = StandardScaler()
        scaler.fit(df_X)
        X_train = scaler.transform(df_X)
    else:
        scaler = None
        X_train = df_X.values

    y_train = df_y.values

    # Create model
    params = model_config.get("params")

    lgbm_params = {
        "learning_rate": params.get("learning_rate"),
        "max_depth": params.get("max_depth"),
        "num_leaves": 32,
        "lambda_l1": params.get("lambda_l1"),
        "lambda_l2": params.get("lambda_l2"),
        "objective": params.get("objective"),
        "metric": {"cross_entropy"},
        "is_unbalance": "true",
        "verbose": 0,
    }

    model = lgbm.train(
        lgbm_params,
        train_set=lgbm.Dataset(X_train, y_train),
        num_boost_round=params.get("num_boost_round"),
    )

    return (model, scaler)


def predict_gb(
    models: Tuple[lgbm.Booster, StandardScaler], df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Use the model(s) to make predictions for the test data.
    """
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        df_X_test = double_columns(df_X_test, shifts)

    scaler = models[1]
    is_scale = scaler is not None

    input_index = df_X_test.index
    if is_scale:
        df_X_test = scaler.transform(df_X_test)
        df_X_test = pd.DataFrame(data=df_X_test, index=input_index)

    df_X_test_nonans = df_X_test.dropna()
    nonans_index = df_X_test_nonans.index

    y_test_hat_nonans = models[0].predict(df_X_test_nonans.values)
    y_test_hat_nonans = pd.Series(data=y_test_hat_nonans, index=nonans_index)

    df_ret = pd.DataFrame(index=input_index)
    df_ret["y_hat"] = y_test_hat_nonans
    sr_ret = df_ret["y_hat"]

    return sr_ret


#
# NN - PyTorch Implementation
#


class SimpleNN(nn.Module):
    def __init__(self, input_size: int, layers: List[int]):
        """
        Initialize the neural network with the given layer sizes.
        """
        super(SimpleNN, self).__init__()
        self.layers = nn.ModuleList()
        # Create layers
        in_features = input_size
        for out_features in layers:
            self.layers.append(nn.Linear(in_features, out_features))
            self.layers.append(nn.Sigmoid())  # Activation function
            in_features = out_features
        self.layers.append(nn.Linear(in_features, 1))  # Output layer
        self.layers.append(nn.Sigmoid())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        """
        for layer in self.layers:
            x = layer(x)
        return x


def train_predict_nn(
    df_X: pd.DataFrame, df_y: pd.Series, df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Train model with the specified hyper-parameters and return its predictions for the test data.
    """
    model_pair = train_nn(df_X, df_y, model_config)
    y_test_hat = predict_nn(model_pair, df_X_test, model_config)
    return y_test_hat


def train_nn(
    df_X: pd.DataFrame, df_y: pd.Series, model_config: dict
) -> Tuple[SimpleNN, StandardScaler]:
    """
    Train a PyTorch neural network with the specified hyper-parameters and return the model (and scaler if any).
    """
    # Double column set if required
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        max_shift = max(shifts)
        df_X = double_columns(df_X, shifts)
        df_X = df_X.iloc[max_shift:]
        df_y = df_y.iloc[max_shift:]

    # Scale
    is_scale = model_config.get("train", {}).get("is_scale", True)
    if is_scale:
        scaler = StandardScaler()
        scaler.fit(df_X)
        X_train = scaler.transform(df_X)
    else:
        scaler = None
        X_train = df_X.values

    y_train = df_y.values

    # Create model
    params = model_config.get("params")
    n_features = X_train.shape[1]
    layers = params.get("layers") or [n_features // 4]
    if not isinstance(layers, list):
        layers = [layers]
    learning_rate = params.get("learning_rate", 0.001)
    n_epochs = params.get("n_epochs", 100)
    batch_size = params.get("bs", 32)

    model = SimpleNN(input_size=n_features, layers=layers)

    # Prepare data for PyTorch
    X_tensor = torch.FloatTensor(X_train)
    y_tensor = torch.FloatTensor(y_train).view(-1, 1)
    dataset = TensorDataset(X_tensor, y_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Train
    model.train()
    for epoch in range(n_epochs):
        for inputs, targets in dataloader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

    return (model, scaler)


def predict_nn(
    models: Tuple[SimpleNN, StandardScaler], df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Use the model(s) to make predictions for the test data.
    """
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        df_X_test = double_columns(df_X_test, shifts)

    scaler = models[1]
    is_scale = scaler is not None

    input_index = df_X_test.index
    if is_scale:
        df_X_test = scaler.transform(df_X_test)
        df_X_test = pd.DataFrame(data=df_X_test, index=input_index)

    df_X_test_nonans = df_X_test.dropna()
    nonans_index = df_X_test_nonans.index

    # Resets all (global) state generated by PyTorch
    torch.cuda.empty_cache()  # Clear GPU memory if necessary

    model = models[0]
    model.eval()
    with torch.no_grad():
        X_tensor = torch.FloatTensor(df_X_test_nonans.values)
        y_test_hat_nonans = model(X_tensor).numpy()

    y_test_hat_nonans = pd.Series(data=y_test_hat_nonans.flatten(), index=nonans_index)

    df_ret = pd.DataFrame(index=input_index)
    df_ret["y_hat"] = y_test_hat_nonans
    sr_ret = df_ret["y_hat"]

    return sr_ret


#
# LC - Linear Classifier
#


def train_predict_lc(
    df_X: pd.DataFrame, df_y: pd.Series, df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Train a Logistic Regression model with the specified hyper-parameters and return its predictions for the test data.
    """
    model_pair = train_lc(df_X, df_y, model_config)
    y_test_hat = predict_lc(model_pair, df_X_test, model_config)
    return y_test_hat


def train_lc(
    df_X: pd.DataFrame, df_y: pd.Series, model_config: dict
) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train a Logistic Regression model with the specified hyper-parameters and return the model (and scaler if any).
    """
    # Double column set if required
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        max_shift = max(shifts)
        df_X = double_columns(df_X, shifts)
        df_X = df_X.iloc[max_shift:]
        df_y = df_y.iloc[max_shift:]

    # Scale
    is_scale = model_config.get("train", {}).get("is_scale", False)
    if is_scale:
        scaler = StandardScaler()
        scaler.fit(df_X)
        X_train = scaler.transform(df_X)
    else:
        scaler = None
        X_train = df_X.values

    y_train = df_y.values

    # Create model
    model = LogisticRegression()

    model.fit(X_train, y_train)

    return (model, scaler)


def predict_lc(
    models: Tuple[LogisticRegression, StandardScaler], df_X_test: pd.DataFrame, model_config: dict
) -> pd.Series:
    """
    Use the model(s) to make predictions for the test data.
    """
    shifts = model_config.get("train", {}).get("shifts", None)
    if shifts:
        df_X_test = double_columns(df_X_test, shifts)

    scaler = models[1]
    is_scale = scaler is not None

    input_index = df_X_test.index
    if is_scale:
        df_X_test = scaler.transform(df_X_test)
        df_X_test = pd.DataFrame(data=df_X_test, index=input_index)

    df_X_test_nonans = df_X_test.dropna()
    nonans_index = df_X_test_nonans.index

    y_test_hat_nonans = models[0].predict(df_X_test_nonans.values)
    y_test_hat_nonans = pd.Series(data=y_test_hat_nonans, index=nonans_index)

    df_ret = pd.DataFrame(index=input_index)
    df_ret["y_hat"] = y_test_hat_nonans
    sr_ret = df_ret["y_hat"]

    return sr_ret


#
# Other supporting functions
#


def double_columns(df: pd.DataFrame, shifts: List[int]) -> pd.DataFrame:
    """
    Create shifted columns in the dataframe based on the specified shifts.
    """
    for shift in shifts:
        for col in df.columns:
            df[f"{col}_shifted_{shift}"] = df[col].shift(shift)
    return df
