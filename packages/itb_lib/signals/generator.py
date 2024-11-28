from typing import Tuple, List
import pandas as pd

from .gen_signals import (
    generate_smoothen_scores,
    generate_combine_scores,
    generate_threshold_rule,
    generate_threshold_rule2,
)


def generate_signals_set(df: pd.DataFrame, fs: dict) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate signals for the input DataFrame based on the provided configuration.
    """
    generator = fs.get("generator")
    gen_config = fs.get("config", {})

    if generator == "smoothen":
        df, features = generate_smoothen_scores(df, gen_config)
    elif generator == "combine":
        df, features = generate_combine_scores(df, gen_config)
    elif generator == "threshold_rule":
        df, features = generate_threshold_rule(df, gen_config)
    elif generator == "threshold_rule2":
        df, features = generate_threshold_rule2(df, gen_config)
    else:
        raise ValueError(f"Unknown signal generator: {generator}")

    return df, features
