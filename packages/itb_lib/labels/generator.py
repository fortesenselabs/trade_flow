from typing import Tuple, List, Dict, Any
import pandas as pd

from .highlow_labels import generate_labels_highlow, generate_labels_highlow2
from .topbot_labels import generate_labels_topbot, generate_labels_topbot2


def generate_labels_set(df: pd.DataFrame, fs: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Generate labels for the input DataFrame based on the provided configuration.

    Args:
        df (pd.DataFrame): The input DataFrame containing data for label generation.
        fs (Dict[str, Any]): Configuration dictionary containing:
            - "generator" (str): The label generator to be used (e.g., "highlow", "highlow2", "topbot", "topbot2").
            - "config" (dict, optional): Additional configuration parameters specific to the label generator.

    Returns:
        Tuple[pd.DataFrame, List[str]]: A tuple containing:
            - Updated DataFrame with labels.
            - List of generated feature/label names.

    Raises:
        ValueError: If an unknown label generator is provided in the configuration.
    """
    generator = fs.get("generator")
    gen_config = fs.get("config", {})

    if generator == "highlow":
        horizon = gen_config.get("horizon")
        print(f"Generating 'highlow' labels with horizon {horizon}...")
        features = generate_labels_highlow(df, horizon=horizon)
        print(f"Finished generating 'highlow' labels. {len(features)} labels generated.")

    elif generator == "highlow2":
        print("Generating 'highlow2' labels...")
        df, features = generate_labels_highlow2(df, gen_config)
        print(f"Finished generating 'highlow2' labels. {len(features)} labels generated.")

    elif generator == "topbot":
        column_name = gen_config.get("columns", "close")
        top_level_fracs = gen_config.get("top_level_fracs", [0.01, 0.02, 0.03, 0.04, 0.05])
        bot_level_fracs = [-x for x in top_level_fracs]
        print(
            f"Generating 'topbot' labels using column '{column_name}' with top level fractions {top_level_fracs}..."
        )
        df, features = generate_labels_topbot(df, column_name, top_level_fracs, bot_level_fracs)
        print(f"Finished generating 'topbot' labels. {len(features)} labels generated.")

    elif generator == "topbot2":
        print("Generating 'topbot2' labels...")
        df, features = generate_labels_topbot2(df, gen_config)
        print(f"Finished generating 'topbot2' labels. {len(features)} labels generated.")

    else:
        raise ValueError(f"Unknown label generator: {generator}")

    return df, features
