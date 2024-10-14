import itertools
from pathlib import Path
import joblib
import torch
import torch.nn as nn

label_algo_separator = "_"

"""
This module provides functionality for loading, saving, and managing machine learning models.
"""


def get_model(name: str, models: list) -> dict:
    """Retrieve a model configuration from the list of models by name.

    Args:
        name (str): The name of the model to retrieve.
        models (list): The list of model configurations.

    Returns:
        dict: The model configuration associated with the given name.
    """
    return next(x for x in models if x.get("name") == name)


def get_algorithm(algorithms: list, name: str) -> dict:
    """Find an algorithm configuration by name from a list of algorithms.

    Args:
        algorithms (list): The list of algorithm configurations.
        name (str): The name of the algorithm to find.

    Returns:
        dict: The algorithm configuration associated with the given name.
    """
    return next(x for x in algorithms if x.get("name") == name)


def save_model_pair(model_path: Path, score_column_name: str, model_pair: tuple) -> None:
    """Save a prediction model and its scaler to files with corresponding extensions.

    Args:
        model_path (Path): The path to save the model files.
        score_column_name (str): The name of the score column for naming conventions.
        model_pair (tuple): A tuple containing the model and the scaler.
    """
    model, scaler = model_pair
    model_path = model_path.absolute()

    # Save scaler
    scaler_file_name = (model_path / score_column_name).with_suffix(".scaler")
    joblib.dump(scaler, scaler_file_name)

    # Save prediction model
    model_extension = ".pt"  # Using .pt for PyTorch models
    model_file_name = (model_path / score_column_name).with_suffix(model_extension)
    torch.save(model.state_dict(), model_file_name)


def load_model_pair(model_path: Path, score_column_name: str) -> tuple:
    """Load a scaler and a prediction model from their respective files.

    Args:
        model_path (Path): The path from which to load the model files.
        score_column_name (str): The name of the score column for naming conventions.

    Returns:
        tuple: A tuple containing the loaded model and scaler.
    """
    model_path = model_path.absolute()

    # Load scaler
    scaler_file_name = (model_path / score_column_name).with_suffix(".scaler")
    scaler = joblib.load(scaler_file_name)

    # Load prediction model
    model_extension = ".pt"
    model_file_name = (model_path / score_column_name).with_suffix(model_extension)
    model = nn.Module()  # Replace with your model class
    model.load_state_dict(torch.load(model_file_name))
    model.eval()  # Set model to evaluation mode

    return model, scaler


def load_models(model_path: Path, labels: list, algorithms: list) -> dict:
    """Load all model pairs for combinations of labels and algorithms into a dictionary.

    Args:
        model_path (Path): The path to the model files.
        labels (list): The list of labels.
        algorithms (list): The list of algorithm configurations.

    Returns:
        dict: A dictionary mapping score column names to model pairs.
    """
    models = {}
    for label_algorithm in itertools.product(labels, algorithms):
        score_column_name = label_algorithm[0] + label_algo_separator + label_algorithm[1]["name"]
        model_pair = load_model_pair(model_path, score_column_name)
        models[score_column_name] = model_pair
    return models


def score_to_label_algo_pair(score_column_name: str) -> tuple:
    """Parse a score column name into its label and algorithm components.

    Args:
        score_column_name (str): The score column name to parse.

    Returns:
        tuple: A tuple containing the label name and algorithm name.
    """
    label_name, algo_name = score_column_name.rsplit(label_algo_separator, 1)
    return label_name, algo_name


# Deprecated. Use these for reference and include in "algorithms" in config instead.
models = [
    {
        "name": "nn",
        "algo": "nn",
        "params": {
            "layers": [29],  # Number of input features (different for spot and future).
            "learning_rate": 0.001,
            "n_epochs": 50,  # Number of epochs for training.
            "bs": 1024,  # Batch size.
        },
        "train": {"is_scale": True, "length": int(3.0 * 525_600), "shifts": []},
        "predict": {"length": "1w"},
    },
    {
        "name": "lc",
        "algo": "lc",
        "params": {
            "penalty": "l2",
            "C": 1.0,
            "class_weight": None,
            "solver": "sag",  # liblinear, lbfgs, sag/saga
            "max_iter": 200,
        },
        "train": {"is_scale": True, "length": int(3.0 * 525_600), "shifts": []},
        "predict": {"length": 1440},
    },
    {
        "name": "gb",
        "algo": "gb",
        "params": {
            "objective": "cross_entropy",
            "max_depth": 1,
            "learning_rate": 0.01,
            "num_boost_round": 1_500,
            "lambda_l1": 1.0,
            "lambda_l2": 1.0,
        },
        "train": {"is_scale": False, "length": int(3.0 * 525_600), "shifts": []},
        "predict": {"length": 1440},
    },
    {
        "name": "gb-y",
        "algo": "gb",
        "params": {
            "objective": "cross_entropy",
            "max_depth": 1,
            "learning_rate": 0.05,
            "num_boost_round": 1_500,
            "lambda_l1": 1.0,
            "lambda_l2": 1.0,
        },
        "train": {"is_scale": True, "length": None, "shifts": []},
        "predict": {"length": 1440},
    },
    {
        "name": "svc-y",
        "algo": "svc",
        "params": {"C": 10.0},
        "train": {"is_scale": True, "length": None, "shifts": []},
        "predict": {"length": 1440},
    },
    {
        "name": "nn_long",
        "algo": "nn",
        "params": {"layers": [29], "learning_rate": 0.001, "n_epochs": 20, "bs": 128},
        "train": {"is_scale": True, "length": int(2.0 * 525_600), "shifts": []},
        "predict": {"length": 0},
    },
    {
        "name": "nn_middle",
        "algo": "nn",
        "params": {"layers": [29], "learning_rate": 0.001, "n_epochs": 20, "bs": 128},
        "train": {"is_scale": True, "length": int(1.5 * 525_600), "shifts": []},
        "predict": {"length": 0},
    },
    {
        "name": "nn_short",
        "algo": "nn",
        "params": {"layers": [29], "learning_rate": 0.001, "n_epochs": 20, "bs": 128},
        "train": {"is_scale": True, "length": int(1.0 * 525_600), "shifts": []},
        "predict": {"length": 0},
    },
]
