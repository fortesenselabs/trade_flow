from keras.layers import Input, Dense, Dropout, Bidirectional, Reshape
from keras.callbacks import EarlyStopping
from keras.metrics import F1Score, FBetaScore, Precision, Recall
from tcn import TCN, tcn_full_summary, compiled_tcn
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_auc_score

# load model
from keras.models import load_model


def import_model(name, directory=".", _format="h5"):
    """
    Import a machine learning model from a file.

    Parameters:
    - name (str): The name of the model to import.
    - directory (str): The directory where the file is located. Default is the current directory.
    - _format (str): The format used for saving the model. Currently supports "h5". Default is "h5".

    Returns:
    - The imported machine learning model.
    """
    if _format == "h5":
        try:
            model = load_model(f"{directory}/{name}.h5")
        except ValueError:
            model = load_model(f"{directory}/{name}.h5", custom_objects={"TCN": TCN})

    return model


def import_all_models(directory=".", file_name="all", _format="h5"):
    """
    Import all machine learning models from a directory.

    Parameters:
    - directory (str): The directory where the files are located. Default is the current directory.
    - file_name (str): The name of the file to import.
    - _format (str): The format used for saving the models. Currently supports "h5". Default is "h5".

    Returns:
    - A dictionary containing all imported machine learning models.
    """
    models = {}
    for file in os.listdir(f"{directory}/"):
        if file.endswith(f".{_format}"):
            name = file.split(f".{_format}")[0]
            if file_name != "all" and file_name in name:
                models[name] = import_model(name, directory, _format)
            else:
                models[name] = import_model(name, directory, _format)

    # pick the latest model in the list
    if len(models) > 1:
        # models_keys = list(models.keys())
        # selected_models = []
        # for i, key in enumerate(models_keys):
        #     if file_name in key:
        #         selected_models.append(key)

        models = {
            k: v
            for k, v in sorted(models.items(), key=lambda item: item[0], reverse=True)
        }
        models = {list(models.keys())[-1]: list(models.values())[-1]}

    return models


def import_model(name, directory=".", _format="h5"):
    """
    Import a machine learning model from a file.

    Parameters:
    - name (str): The name of the model to import.
    - directory (str): The directory where the file is located. Default is the current directory.
    - _format (str): The format used for saving the model. Currently supports "h5". Default is "h5".

    Returns:
    - The imported machine learning model.
    """
    if _format == "h5":
        try:
            model = load_model(f"{directory}/{name}.h5")
        except ValueError:
            model = load_model(f"{directory}/{name}.h5", custom_objects={"TCN": TCN})

    return model


def import_all_models(directory=".", file_name="all", _format="h5"):
    """
    Import all machine learning models from a directory.

    Parameters:
    - directory (str): The directory where the files are located. Default is the current directory.
    - file_name (str): The name of the file to import.
    - _format (str): The format used for saving the models. Currently supports "h5". Default is "h5".

    Returns:
    - A dictionary containing all imported machine learning models.
    """
    models = {}
    for file in os.listdir(f"{directory}/"):
        if file.endswith(f".{_format}"):
            name = file.split(f".{_format}")[0]
            if file_name != "all" and file_name in name:
                if name.split("_")[-1].isdigit():
                    models[name] = None
            else:
                models[name] = import_model(name, directory, _format)

    # pick the latest model in the list
    if len(models) > 1 and file_name != "all":
        models = {
            k: v
            for k, v in sorted(models.items(), key=lambda item: item[0], reverse=True)
        }
        models[list(models.keys())[-1]] = import_model(name, directory, _format)

    return models


import_all_models(directory="../models", file_name="Step Index")
