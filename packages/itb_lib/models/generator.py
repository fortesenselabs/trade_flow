from typing import Tuple

import numpy as np
import pandas as pd

from common.classifiers import *
from common.model_store import *
from common.gen_features import *
from common.gen_labels_highlow import generate_labels_highlow, generate_labels_highlow2
from common.gen_labels_topbot import generate_labels_topbot, generate_labels_topbot2
from common.gen_signals import (
    generate_smoothen_scores,
    generate_combine_scores,
    generate_threshold_rule,
    generate_threshold_rule2,
)


def predict_feature_set(df, fs, config, models: dict):

    labels = fs.get("config").get("labels")
    if not labels:
        labels = config.get("labels")

    algorithms = fs.get("config").get("functions")
    if not algorithms:
        algorithms = fs.get("config").get("algorithms")
    if not algorithms:
        algorithms = config.get("algorithms")

    train_features = fs.get("config").get("columns")
    if not train_features:
        train_features = fs.get("config").get("features")
    if not train_features:
        train_features = config.get("train_features")

    train_df = df[train_features]

    features = []
    scores = dict()
    out_df = pd.DataFrame(index=train_df.index)  # Collect predictions

    for label in labels:
        for model_config in algorithms:

            algo_name = model_config.get("name")
            algo_type = model_config.get("algo")
            score_column_name = label + label_algo_separator + algo_name
            algo_train_length = model_config.get("train", {}).get("length")

            # It is an entry from loaded model dict
            model_pair = models.get(score_column_name)  # Trained model from model registry

            print(
                f"Predict '{score_column_name}'. Algorithm {algo_name}. Label: {label}. Train length {len(train_df)}. Train columns {len(train_df.columns)}"
            )

            if algo_type == "gb":
                df_y_hat = predict_gb(model_pair, train_df, model_config)
            elif algo_type == "nn":
                df_y_hat = predict_nn(model_pair, train_df, model_config)
            elif algo_type == "lc":
                df_y_hat = predict_lc(model_pair, train_df, model_config)
            elif algo_type == "svc":
                df_y_hat = predict_svc(model_pair, train_df, model_config)
            else:
                raise ValueError(f"Unknown algorithm type '{algo_type}'")

            out_df[score_column_name] = df_y_hat
            features.append(score_column_name)

            # For each new score, compare it with the label true values
            if label in df:
                scores[score_column_name] = compute_scores(df[label], df_y_hat)

    return out_df, features, scores


def train_feature_set(df, fs, config):

    labels = fs.get("config").get("labels")
    if not labels:
        labels = config.get("labels")

    algorithms = fs.get("config").get("functions")
    if not algorithms:
        algorithms = fs.get("config").get("algorithms")
    if not algorithms:
        algorithms = config.get("algorithms")

    train_features = fs.get("config").get("columns")
    if not train_features:
        train_features = fs.get("config").get("features")
    if not train_features:
        train_features = config.get("train_features")

    models = dict()
    scores = dict()
    out_df = pd.DataFrame()  # Collect predictions

    for label in labels:
        for model_config in algorithms:

            algo_name = model_config.get("name")
            algo_type = model_config.get("algo")
            score_column_name = label + label_algo_separator + algo_name
            algo_train_length = model_config.get("train", {}).get("length")

            # Limit length according to the algorith parameters
            if algo_train_length:
                train_df = df.tail(algo_train_length)
            else:
                train_df = df
            df_X = train_df[train_features]
            df_y = train_df[label]

            print(
                f"Train '{score_column_name}'. Algorithm {algo_name}. Label: {label}. Train length {len(df_X)}. Train columns {len(df_X.columns)}"
            )

            if algo_type == "gb":
                model_pair = train_gb(df_X, df_y, model_config)
                models[score_column_name] = model_pair
                df_y_hat = predict_gb(model_pair, df_X, model_config)
            elif algo_type == "nn":
                model_pair = train_nn(df_X, df_y, model_config)
                models[score_column_name] = model_pair
                df_y_hat = predict_nn(model_pair, df_X, model_config)
            elif algo_type == "lc":
                model_pair = train_lc(df_X, df_y, model_config)
                models[score_column_name] = model_pair
                df_y_hat = predict_lc(model_pair, df_X, model_config)
            elif algo_type == "svc":
                model_pair = train_svc(df_X, df_y, model_config)
                models[score_column_name] = model_pair
                df_y_hat = predict_svc(model_pair, df_X, model_config)
            else:
                print(f"ERROR: Unknown algorithm type {algo_type}. Check algorithm list.")
                return

            scores[score_column_name] = compute_scores(df_y, df_y_hat)
            out_df[score_column_name] = df_y_hat

    return out_df, models, scores


def resolve_generator_name(gen_name: str):
    """
    Resolve the specified name to a function reference.
    Fully qualified name consists of module name and function name separated by a colon,
    for example:  'mod1.mod2.mod3:my_func'.

    Example: fn = resolve_generator_name("common.gen_features_topbot:generate_labels_topbot3")
    """

    mod_and_func = gen_name.split(":", 1)
    mod_name = mod_and_func[0] if len(mod_and_func) > 1 else None
    func_name = mod_and_func[-1]

    if not mod_name:
        return None

    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        return None
    if mod is None:
        return None

    try:
        func = getattr(mod, func_name)
    except AttributeError as e:
        return None

    return func
