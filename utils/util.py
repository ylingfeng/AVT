import json
import time

import numpy as np


def unique_elements_with_indices(ids):
    ids_array = np.array(ids)
    _, unique_indices = np.unique(ids_array, return_index=True)
    unique_ids = ids_array[unique_indices]

    return unique_ids.tolist(), unique_indices.tolist()


def json_loader(path):
    with open(path, "r") as f:
        obj = json.load(f)
    print(f"load {path}")
    return obj


def json_saver(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"save {path}")


def get_time():
    creat_time = str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
    return creat_time
