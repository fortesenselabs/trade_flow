from pathlib import Path
from datetime import datetime

import pandas as pd
import click

from application.config.settings import Settings
from application.logger import AppLogger
from application.models.app_model import AppConfig
from application.analyzers.processors.generators import generate_feature_set

"""
This script will load a feature file (or any file with close price), and add
top-bot columns according to the label parameter, by finally storing both input
data and the labels in the output file (can be the same file as input).
"""


logger = AppLogger(name=__name__)


#
# Parameters
#
class P:
    in_nrows = 100_000_000
    tail_rows = 0  # Process only this number of last rows


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def main(config_file):
    """
    Load a file with close price (typically feature matrix),
    compute top-bottom labels, add them to the data, and store to output file.
    """
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    app_config: AppConfig = settings.get_app_config()

    time_column = app_config.config.time_column

    now = datetime.now()

    #
    # Load merged data with regular time series
    #
    symbol = app_config.config.symbol
    data_path = Path(app_config.config.data_folder) / symbol

    file_path = data_path / app_config.config.feature_file_name
    if not file_path.is_file():
        logger.error(f"Data file does not exist: {file_path}")
        return

    logger.info(f"Loading data from source data file {file_path}...")
    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(
            file_path,
            parse_dates=[time_column],
            date_format="ISO8601",
            nrows=P.in_nrows,
        )
    else:
        logger.error(
            f"ERROR: Unknown extension of the 'feature_file_name' file '{file_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return
    logger.info(f"Finished loading {len(df)} records with {len(df.columns)} columns.")

    df = df.iloc[-P.tail_rows :]
    df = df.reset_index(drop=True)

    logger.info(
        f"Input data size {len(df)} records. Range: [{df.iloc[0][time_column]}, {df.iloc[-1][time_column]}]"
    )

    #
    # Generate derived features
    #
    label_sets = app_config.config.label_sets
    if not label_sets:
        logger.error(f"ERROR: no label sets defined. Nothing to process.")
        return

    # Apply all feature generators to the data frame which get accordingly new derived columns
    # The feature parameters will be taken from App.config (depending on generator)
    logger.info(f"Start generating labels for {len(df)} input records.")

    all_features = []
    for i, fs in enumerate(label_sets):
        fs_now = datetime.now()
        _fs = fs.model_dump()
        logger.info(
            f"Start label set {i}/{len(label_sets)}. Generator {_fs.get('generator')}..."
        )
        df, new_features = generate_feature_set(df, _fs, last_rows=0)
        all_features.extend(new_features)
        fs_elapsed = datetime.now() - fs_now
        logger.info(
            f"Finished label set {i}/{len(label_sets)}. Generator {_fs.get('generator')}. Labels: {len(new_features)}. Time: {str(fs_elapsed).split('.')[0]}"
        )

    logger.info(f"Finished generating labels.")

    logger.info(f"Number of NULL values:")
    logger.info(df[all_features].isnull().sum().sort_values(ascending=False))

    #
    # Store feature matrix in output file
    #
    out_file_name = app_config.config.matrix_file_name
    out_path = (data_path / out_file_name).resolve()

    logger.info(
        f"Storing file with labels. {len(df)} records and {len(df.columns)} columns in output file {out_path}..."
    )
    if out_path.suffix == ".parquet":
        df.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df.to_csv(out_path, index=False, float_format="%.6f")
    else:
        logger.error(
            f"ERROR: Unknown extension of the 'matrix_file_name' file '{out_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    logger.info(f"Stored output file {out_path} with {len(df)} records")

    #
    # Store labels
    #
    with open(out_path.with_suffix(".txt"), "a+") as f:
        f.write(", ".join([f'"{f}"' for f in all_features]) + "\n\n")

    logger.info(
        f"Stored {len(all_features)} labels in output file {out_path.with_suffix('.txt')}"
    )

    elapsed = datetime.now() - now
    logger.info(
        f"Finished generating {len(all_features)} labels in {str(elapsed).split('.')[0]}. Time per label: {str(elapsed/len(all_features)).split('.')[0]}"
    )


if __name__ == "__main__":
    main()
