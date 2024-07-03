import click
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from tradeflow.evaluators import (
    compute_scores,
    train_predict_gb,
    train_predict_nn,
    train_predict_lc,
    train_predict_svc,
)
from application.config import Settings
from application.logger import AppLogger
from application.models import AppConfig
from application.utils import find_index
from application.database import score_to_label_algo_pair


logger = AppLogger(name=__name__)

"""
Generate label predictions for the whole input feature matrix by iteratively training models using historic data and predicting labels for some future horizon.
The main parameter is the step of iteration, that is, the future horizon for prediction.
As usual, we can specify past history length used to train a model.
The output file will store predicted labels in addition to all input columns (generated features and true labels).

This file is intended for training signal models (by simulating trade process and computing overall performance for some long period).
The output predicted labels will cover shorter period of time because we need some relatively long history to train the very first model.
"""


#
# Parameters
#
class P:
    in_nrows = 100_000_000


label_algo_separator = "_"

#
# Main
#


@click.command()
@click.option(
    "--config_file", "-c", type=click.Path(), default="", help="Configuration file name"
)
def main(config_file):
    settings: Settings = Settings(config_file)
    logger.info(settings.model_dump())

    app_config: AppConfig = settings.get_app_config()

    time_column = app_config.config.time_column

    now = datetime.now()

    rp_config = app_config.config.rolling_predict

    use_multiprocessing = rp_config.use_multiprocessing
    max_workers = rp_config.max_workers

    #
    # Load feature matrix
    #
    symbol = app_config.config.symbol
    data_path = Path(app_config.config.data_folder) / symbol

    file_path = data_path / app_config.config.matrix_file_name
    if not file_path.is_file():
        logger.error(f"ERROR: Input file does not exist: {file_path}")
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
            f"ERROR: Unknown extension of the 'matrix_file_name' file '{file_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return
    logger.info(f"Finished loading {len(df)} records with {len(df.columns)} columns.")

    #
    # Limit the source data
    #

    data_start = rp_config.data_start
    if isinstance(data_start, str):
        data_start = find_index(df, data_start)
    data_end = rp_config.data_end
    if isinstance(data_end, str):
        data_end = find_index(df, data_end)

    df = df.iloc[data_start:data_end]
    df = df.reset_index(drop=True)

    logger.info(
        f"Input data size {len(df)} records. Range: [{df.iloc[0][time_column]}, {df.iloc[-1][time_column]}]"
    )

    #
    # Determine parameters of the rolling prediction loop
    #

    prediction_start = rp_config.prediction_start
    if isinstance(prediction_start, str):
        prediction_start = find_index(df, prediction_start)
    prediction_size = rp_config.prediction_size
    prediction_steps = rp_config.prediction_steps

    # Compute a missing parameter if any
    if not prediction_start:
        if not prediction_size or not prediction_steps:
            raise ValueError(
                f"Only one of the three rolling prediction loop parameters can be empty."
            )
        # Where we have to start in order to perform the specified number of steps each having the specified length
        prediction_start = len(df) - prediction_size * prediction_steps
    elif not prediction_size:
        if not prediction_start or not prediction_steps:
            raise ValueError(
                f"Only one of the three rolling prediction loop parameters can be empty."
            )
        # Size of one prediction in order to get the specified number of steps with the specified length
        prediction_size = (len(df) - prediction_start) // prediction_steps
    elif not prediction_steps:
        if not prediction_start or not prediction_size:
            raise ValueError(
                f"Only one of the three rolling prediction loop parameters can be empty."
            )
        # Number of steps with the specified length with the specified start
        prediction_steps = (len(df) - prediction_start) // prediction_size

    # Check consistency of the loop parameters
    if len(df) - prediction_start < prediction_steps * prediction_size:
        raise ValueError(
            f"Not enough data for {prediction_steps} steps each of size {prediction_size} starting from {prediction_start}. Available data for prediction: {len(df) - prediction_start}"
        )

    #
    # Prepare data by selecting columns and rows
    #
    label_horizon = (
        app_config.config.label_horizon
    )  # Labels are generated from future data and hence we might want to explicitly remove some tail rows
    train_length = app_config.config.train_length
    train_features = app_config.config.train_features
    labels = app_config.config.labels
    algorithms = app_config.config.algorithms

    # Select necessary features and label
    out_columns = [time_column, "open", "high", "low", "close", "volume", "close_time"]
    out_columns = [x for x in out_columns if x in df.columns]
    labels_present = set(labels).issubset(df.columns)
    if labels_present:
        all_features = train_features + labels
    else:
        all_features = train_features
    df = df[out_columns + [x for x in all_features if x not in out_columns]]

    for label in labels:
        # "category" NN does not work without this (note that we assume a classification task here)
        df[label] = df[label].astype(int)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # in_df = in_df.dropna(subset=labels)
    df = df.reset_index(
        drop=True
    )  # We must reset index after removing rows to remove gaps

    # Result rows. Here store only rows for which we make predictions
    labels_hat_df = pd.DataFrame()

    logger.info(
        f"Start index: {prediction_start}. Number of steps: {prediction_steps}. Step size: {prediction_size}"
    )
    logger.info(f"Starting rolling predict loop...")

    for step in range(prediction_steps):

        # Predict data

        predict_start = prediction_start + (step * prediction_size)
        predict_end = predict_start + prediction_size

        predict_df = df.iloc[
            predict_start:predict_end
        ]  # We assume that iloc is equal to index
        # predict_df = predict_df.dropna(subset=features)  # Nans will be droped by the algorithms themselves

        # Here we will collect predicted columns
        predict_labels_df = pd.DataFrame(index=predict_df.index)

        # Predict data

        df_X_test = predict_df[train_features]
        # df_y_test = predict_df[predict_label]  # It will be set in the loop over labels

        # Train data

        # We exclude recent objects from training, because they do not have labels yet - the labels are in future
        # In real (stream) data, we will have null labels for recent objects. During simulation, labels are available and hence we need to ignore/exclude them manually
        train_end = predict_start - label_horizon - 1
        if train_length:
            train_start = max(0, train_end - train_length)
        else:
            train_start = 0

        train_df = df.iloc[
            train_start:train_end
        ]  # We assume that iloc is equal to index
        train_df = train_df.dropna(subset=train_features)

        logger.info(
            f"\n===>>> Start step {step}/{prediction_steps}. Train range: [{train_start}, {train_end}]={train_end-train_start}. Prediction range: [{predict_start}, {predict_end}]={predict_end-predict_start}. Jobs/scores: {len(labels)*len(algorithms)}. {use_multiprocessing=} "
        )

        step_start_time = datetime.now()

        if use_multiprocessing:

            execution_results = dict()
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit train-predict label-algorithms jobs to the pool
                for (
                    label
                ) in (
                    labels
                ):  # Train-predict different labels (and algorithms) using same X
                    for model_config in algorithms:
                        algo_name = model_config.name
                        algo_type = model_config.algo
                        algo_train_length = model_config.train.length
                        score_column_name = label + label_algo_separator + algo_name

                        # Limit length according to algorith parameters
                        if algo_train_length:
                            train_df_2 = train_df.tail(algo_train_length)
                        else:
                            train_df_2 = train_df
                        df_X = train_df_2[train_features]
                        df_y = train_df_2[label]
                        df_y_test = predict_df[label]

                        if algo_type == "gb":
                            execution_results[score_column_name] = executor.submit(
                                train_predict_gb,
                                df_X,
                                df_y,
                                df_X_test,
                                model_config.model_dump(),
                            )
                        elif algo_type == "nn":
                            execution_results[score_column_name] = executor.submit(
                                train_predict_nn,
                                df_X,
                                df_y,
                                df_X_test,
                                model_config.model_dump(),
                            )
                        elif algo_type == "lc":
                            execution_results[score_column_name] = executor.submit(
                                train_predict_lc,
                                df_X,
                                df_y,
                                df_X_test,
                                model_config.model_dump(),
                            )
                        elif algo_type == "svc":
                            execution_results[score_column_name] = executor.submit(
                                train_predict_svc,
                                df_X,
                                df_y,
                                df_X_test,
                                model_config.model_dump(),
                            )
                        else:
                            logger.error(
                                f"ERROR: Unknown algorithm type {algo_type}. Check algorithm list."
                            )
                            return

                # Wait for the job finish and collect their results
                for score_column_name, future in execution_results.items():
                    predict_labels_df[score_column_name] = future.result()
                    if future.exception():
                        logger.exception(
                            f"Exception while train-predict {score_column_name}."
                        )
                        return

        else:  # No multiprocessing - sequential execution

            for (
                label
            ) in labels:  # Train-predict different labels (and algorithms) using same X
                for model_config in algorithms:
                    algo_name = model_config.name
                    algo_type = model_config.algo
                    algo_train_length = model_config.train.length
                    score_column_name = label + label_algo_separator + algo_name

                    # Limit length according to algorith parameters
                    if algo_train_length:
                        train_df_2 = train_df.tail(algo_train_length)
                    else:
                        train_df_2 = train_df
                    df_X = train_df_2[train_features]
                    df_y = train_df_2[label]
                    df_y_test = predict_df[label]

                    if algo_type == "gb":
                        predict_labels_df[score_column_name] = train_predict_gb(
                            df_X, df_y, df_X_test, model_config.model_dump()
                        )
                    elif algo_type == "nn":
                        predict_labels_df[score_column_name] = train_predict_nn(
                            df_X, df_y, df_X_test, model_config.model_dump()
                        )
                    elif algo_type == "lc":
                        predict_labels_df[score_column_name] = train_predict_lc(
                            df_X, df_y, df_X_test, model_config.model_dump()
                        )
                    elif algo_type == "svc":
                        predict_labels_df[score_column_name] = train_predict_svc(
                            df_X, df_y, df_X_test, model_config.model_dump()
                        )
                    else:
                        logger.error(
                            f"ERROR: Unknown algorithm type {algo_type}. Check algorithm list."
                        )
                        return

        #
        # Append predicted *rows* to the end of previous predicted rows
        #

        # Predictions for all labels and histories (and algorithms) have been generated for the iteration
        labels_hat_df = pd.concat([labels_hat_df, predict_labels_df])

        elapsed = datetime.now() - step_start_time
        logger.info(
            f"End step {step}/{prediction_steps}. Scores predicted: {len(predict_labels_df.columns)}. Time elapsed: {str(elapsed).split('.')[0]}"
        )

    # End of loop over prediction steps
    logger.info("")
    logger.info(
        f"Finished all {prediction_steps} prediction steps each with {prediction_size} predicted rows (stride). "
    )
    logger.info(
        f"Size of predicted dataframe {len(labels_hat_df)}. Number of rows in all steps {prediction_steps*prediction_size} (steps * stride). "
    )
    logger.info(f"Number of predicted columns {len(labels_hat_df.columns)}")

    #
    # Store data
    #
    # We do not store features. Only selected original data, labels, and their predictions
    out_df = labels_hat_df.join(df[out_columns + labels])

    # out_path = data_path / app_config.config.predict_file_name
    out_path = data_path / app_config.config.signal_file_name

    logger.info(
        f"Storing predictions with {len(out_df)} records and {len(out_df.columns)} columns in output file {out_path}..."
    )
    if out_path.suffix == ".parquet":
        out_df.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        out_df.to_csv(out_path, index=False, float_format="%.6f")
    else:
        logger.info(
            f"ERROR: Unknown extension of the 'predict_file_name' file '{out_path.suffix}'. Only 'csv' and 'parquet' are supported"
        )
        return

    logger.info(
        f"Predictions stored in file: {out_path}. Length: {len(out_df)}. Columns: {len(out_df.columns)}"
    )

    #
    # Compute accuracy for the whole data set (all segments)
    #

    score_lines = []
    for score_column_name in labels_hat_df.columns:
        label_column, _ = score_to_label_algo_pair(score_column_name)

        # Drop nans from scores
        df_scores = pd.DataFrame(
            {"y_true": out_df[label_column], "y_predicted": out_df[score_column_name]}
        )
        df_scores = df_scores.dropna()

        y_true = df_scores["y_true"].astype(int)
        y_predicted = df_scores["y_predicted"]
        y_predicted_class = np.where(y_predicted.values > 0.5, 1, 0)

        logger.info(f"Using {len(df_scores)} non-nan rows for scoring.")

        score = compute_scores(y_true, y_predicted)

        score_lines.append(
            f"{score_column_name}, {score.get('auc'):.3f}, {score.get('ap'):.3f}, {score.get('f1'):.3f}, {score.get('precision'):.3f}, {score.get('recall'):.3f}"
        )

    #
    # Store hyper-parameters and scores
    #
    with open(out_path.with_suffix(".txt"), "a+") as f:
        f.write("\n".join([str(x) for x in score_lines]) + "\n\n")

    elapsed = datetime.now() - now
    logger.info(f"Finished rolling prediction in {str(elapsed).split('.')[0]}")


if __name__ == "__main__":
    main()
