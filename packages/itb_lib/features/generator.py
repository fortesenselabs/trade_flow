from typing import Tuple, List
import pandas as pd

from packages.itb_lib.labels import generate_labels_set
from packages.itb_lib.signals import generate_signals_set
from packages.itb_lib.utils import resolve_generator_name

from .depth_features import generate_features_depth
from .itblib_features import generate_features_itblib
from .itbstats_features import generate_features_itbstats
from .talib_features import generate_features_talib
from .tsfresh_features import generate_features_tsfresh


"""
Feature generators. 
A feature generator knows how to generate features from its declarative specification in the config file.
"""


def generate_features_set(
    df: pd.DataFrame, fs: dict, last_rows: int
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate features for the input DataFrame based on the provided configuration.
    """
    cp = fs.get("column_prefix")
    if cp:
        cp = cp + "_"
        f_cols = [col for col in df if col.startswith(cp)]
        f_df = df[f_cols].rename(columns=lambda x: x[len(cp) :] if x.startswith(cp) else x)
    else:
        f_df = df.copy()

    generator = fs.get("generator")
    gen_config = fs.get("config", {})

    if generator == "itblib":
        features = generate_features_itblib(f_df, gen_config, last_rows=last_rows)
    elif generator == "depth":
        features = generate_features_depth(f_df)
    elif generator == "tsfresh":
        features = generate_features_tsfresh(f_df, gen_config, last_rows=last_rows)
    elif generator == "talib":
        features = generate_features_talib(f_df, gen_config, last_rows=last_rows)
    elif generator == "itbstats":
        features = generate_features_itbstats(f_df, gen_config, last_rows=last_rows)
    else:
        # Resolve generator name to a function reference
        generator_fn = resolve_generator_name(generator)
        if generator_fn is None:
            raise ValueError(
                f"Unknown feature generator name or name cannot be resolved: {generator}"
            )
        f_df, features = generator_fn(f_df, gen_config)

    # Prefix new features
    fp = fs.get("feature_prefix")
    if fp:
        f_df = f_df.add_prefix(fp + "_")

    new_features = f_df.columns.to_list()

    # Remove existing columns if any
    df.drop(list(set(df.columns) & set(new_features)), axis=1, inplace=True)

    df = df.join(f_df)  # Attach derived features
    return df, new_features


def generate_feature_set(
    df: pd.DataFrame, fs: dict, last_rows: int
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate features, labels, and signals for the input DataFrame based on the provided configuration.
    """
    df, feature_columns = generate_features_set(df, fs, last_rows)
    df, label_columns = generate_labels_set(df, fs)
    df, signal_columns = generate_signals_set(df, fs)

    return df, feature_columns + label_columns + signal_columns
