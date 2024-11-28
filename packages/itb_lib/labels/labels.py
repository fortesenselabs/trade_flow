from pathlib import Path
from datetime import datetime
import pandas as pd
from packages.itb_lib.features import generate_feature_set


class P:
    """
    Parameters for data loading and processing.
    """

    in_nrows = 100_000_000  # Number of rows to load from the data file.
    tail_rows = 0  # Number of last rows to process.


def get_features(
    data_folder: str, symbol: str, time_column: str, feature_file_name: str, feature_sets: list
):
    """
    Load a feature matrix from a specified file, generate new features based on
    the defined feature sets, and store the augmented data to an output file.

    Parameters:
        data_folder (str): Path to the data folder.
        symbol (str): Symbol for which to load data.
        time_column (str): Name of the time column in the dataset.
        feature_file_name (str): Name of the feature file to load.
        feature_sets (list): List of feature set configurations.
    """
    now = datetime.now()

    # Load merged data with regular time series
    data_path = Path(data_folder) / symbol
    file_path = data_path / feature_file_name

    if not file_path.is_file():
        print(f"Data file does not exist: {file_path}")
        return

    print(f"Loading data from source data file {file_path}...")
    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(
            file_path, parse_dates=[time_column], date_format="ISO8601", nrows=P.in_nrows
        )
    else:
        print(
            f"ERROR: Unknown extension of the 'feature_file_name' file '{file_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    print(f"Finished loading {len(df)} records with {len(df.columns)} columns.")
    df = df.iloc[-P.tail_rows :].reset_index(drop=True)
    print(
        f"Input data size {len(df)} records. Range: [{df.iloc[0][time_column]}, {df.iloc[-1][time_column]}]"
    )

    if not feature_sets:
        print(f"ERROR: no feature sets defined. Nothing to process.")
        return

    # Generate features
    print(f"Start generating features for {len(df)} input records.")
    all_features = []

    for i, fs in enumerate(feature_sets):
        fs_now = datetime.now()
        print(f"Start feature set {i}/{len(feature_sets)}. Generator {fs.get('generator')}...")
        df, new_features = generate_feature_set(df, fs, last_rows=0)
        all_features.extend(new_features)
        fs_elapsed = datetime.now() - fs_now
        print(
            f"Finished feature set {i}/{len(feature_sets)}. Generator {fs.get('generator')}. Features: {len(new_features)}. Time: {str(fs_elapsed).split('.')[0]}"
        )

    print(f"Finished generating features.")
    print(f"Number of NULL values:")
    print(df[all_features].isnull().sum().sort_values(ascending=False))

    # Store feature matrix in output file
    out_file_name = feature_file_name
    out_path = (data_path / out_file_name).resolve()

    print(
        f"Storing features with {len(df)} records and {len(df.columns)} columns in output file {out_path}..."
    )
    if out_path.suffix == ".parquet":
        df.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df.to_csv(out_path, index=False, float_format="%.6f")
    else:
        print(
            f"ERROR: Unknown extension of the 'feature_file_name' file '{out_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    print(f"Stored output file {out_path} with {len(df)} records")

    # Store feature list
    with open(out_path.with_suffix(".txt"), "a+") as f:
        f.write(", ".join([f'"{f}"' for f in all_features]) + "\n\n")

    print(f"Stored {len(all_features)} features in output file {out_path.with_suffix('.txt')}")

    elapsed = datetime.now() - now
    print(
        f"Finished generating {len(all_features)} features in {str(elapsed).split('.')[0]}. Time per feature: {str(elapsed/len(all_features)).split('.')[0]}"
    )


def get_labels(
    data_folder: str,
    symbol: str,
    time_column: str,
    feature_file_name: str,
    label_sets: list,
    matrix_file_name: str,
):
    """
    Load a file with close price (typically feature matrix), compute top-bottom labels,
    add them to the data, and store to output file.

    Parameters:
        data_folder (str): Path to the data folder.
        symbol (str): Symbol for which to load data.
        time_column (str): Name of the time column in the dataset.
        feature_file_name (str): Name of the feature file to load.
        label_sets (list): List of label set configurations.
        matrix_file_name (str): Name of the output file to store labels.
    """
    now = datetime.now()

    # Load merged data with regular time series
    data_path = Path(data_folder) / symbol
    file_path = data_path / feature_file_name

    if not file_path.is_file():
        print(f"Data file does not exist: {file_path}")
        return

    print(f"Loading data from source data file {file_path}...")
    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(
            file_path, parse_dates=[time_column], date_format="ISO8601", nrows=P.in_nrows
        )
    else:
        print(
            f"ERROR: Unknown extension of the 'feature_file_name' file '{file_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    print(f"Finished loading {len(df)} records with {len(df.columns)} columns.")
    df = df.iloc[-P.tail_rows :].reset_index(drop=True)
    print(
        f"Input data size {len(df)} records. Range: [{df.iloc[0][time_column]}, {df.iloc[-1][time_column]}]"
    )

    if not label_sets:
        print(f"ERROR: no label sets defined. Nothing to process.")
        return

    # Generate labels
    print(f"Start generating labels for {len(df)} input records.")
    all_features = []

    for i, ls in enumerate(label_sets):
        fs_now = datetime.now()
        print(f"Start label set {i}/{len(label_sets)}. Generator {ls.get('generator')}...")
        df, new_features = generate_feature_set(df, ls, last_rows=0)
        all_features.extend(new_features)
        fs_elapsed = datetime.now() - fs_now
        print(
            f"Finished label set {i}/{len(label_sets)}. Generator {ls.get('generator')}. Labels: {len(new_features)}. Time: {str(fs_elapsed).split('.')[0]}"
        )

    print(f"Finished generating labels.")
    print(f"Number of NULL values:")
    print(df[all_features].isnull().sum().sort_values(ascending=False))

    # Store feature matrix in output file
    out_file_name = matrix_file_name
    out_path = (data_path / out_file_name).resolve()

    print(
        f"Storing file with labels. {len(df)} records and {len(df.columns)} columns in output file {out_path}..."
    )
    if out_path.suffix == ".parquet":
        df.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df.to_csv(out_path, index=False, float_format="%.6f")
    else:
        print(
            f"ERROR: Unknown extension of the 'matrix_file_name' file '{out_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    print(f"Stored output file {out_path} with {len(df)} records")

    # Store labels
    with open(out_path.with_suffix(".txt"), "a+") as f:
        f.write(", ".join([f'"{f}"' for f in all_features]) + "\n\n")

    print(f"Stored {len(all_features)} labels in output file {out_path.with_suffix('.txt')}")

    elapsed = datetime.now() - now
    print(
        f"Finished generating {len(all_features)} labels in {str(elapsed).split('.')[0]}. Time per label: {str(elapsed/len(all_features)).split('.')[0]}"
    )
