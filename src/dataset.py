from abc import abstractmethod
import json
from pathlib import Path

DATA_DIR = Path('data')

class Dataset:
    @abstractmethod
    def read_task(self, task_id):
        return

    @abstractmethod
    def string_encode(self):
        return
    
    @abstractmethod
    def get_all_task_ids(self):
        return

class LocalDataset(Dataset):
    def __init__(self, dataset_location, _DATA_DIR = DATA_DIR):
        self.DATA_DIR = _DATA_DIR
        self.dataset_location = dataset_location
    
    def read_task(self, task_id):
        json_text = (self.DATA_DIR / self.dataset_location / f'{task_id}.json').read_text()
        return json.loads(json_text)
    
    def string_encode(self):
        return f'LOCAL_DATASET:{self.DATA_DIR}:{self.dataset_location}'
    
    def get_all_task_ids(self):
        return list(p.stem for p in (self.DATA_DIR / self.dataset_location).iterdir())

class KaggleDataset(Dataset):
    def __init__(self, dataset_location, _DATA_DIR):
        self.DATA_DIR = Path(_DATA_DIR)
        self.dataset_location = dataset_location

    def read_task(self, task_id):
        with open (self.DATA_DIR / self.dataset_location, 'r') as f:
           dataset = json.load(f)
        return dataset[task_id]

    def string_encode(self):
        return f'KAGGLE_DATASET:{self.DATA_DIR}:{self.dataset_location}'
    
    def get_all_task_ids(self):
        with open (self.DATA_DIR / self.dataset_location, 'r') as f:
           dataset = json.load(f)
        return list(dataset.keys())


def load_dataset(dataset_descriptor):
    type, dr, location = dataset_descriptor.split(':')
    if type == 'LOCAL_DATASET':
        return LocalDataset(location, Path(dr))
    else:
        return KaggleDataset(location, Path(dr))