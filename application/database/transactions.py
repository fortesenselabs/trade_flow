import pandas as pd
from pathlib import Path
from datetime import datetime


def load_last_transaction(transaction_file: Path):
    # Initialize the default transaction dictionary
    t_dict = {
        "timestamp": str(datetime.now()),
        "price": 0.0,
        "profit": 0.0,
        "status": "",
    }

    # Check if the transaction file exists
    if transaction_file.is_file():
        with open(transaction_file, "r") as f:
            lines = f.readlines()

        if lines:
            last_line = lines[-1].strip()
            if last_line:
                keys = ["timestamp", "price", "profit", "status"]
                values = last_line.split(",")
                t_dict.update(dict(zip(keys, values)))
                t_dict["price"] = float(t_dict["price"])
                t_dict["profit"] = float(t_dict["profit"])

    return t_dict


def load_all_transactions(transaction_file: Path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(
        transaction_file, names=["timestamp", "price", "profit", "status"], header=None
    )

    # Convert the 'timestamp' column to datetime objects
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

    return df
