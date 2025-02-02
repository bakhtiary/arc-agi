from unittest import TestCase
from pathlib import Path

from dataset import KaggleDataset, LocalDataset


class KaggleDatasetTest(TestCase):
    def test_read_task(self):
        ds = KaggleDataset('arc-agi_training_challenges.json', Path('data/kaggle') )
        task = ds.read_task('c8f0f002')
        assert 'input' in task['test'][0]

    def test_get_all_task_ids(self):
        ds = KaggleDataset('arc-agi_training_challenges.json', Path('data/kaggle') )
        self.assertEqual(len(ds.get_all_task_ids()), 400)


class LocalDatasetTest(TestCase):
    def test_read_task(self):
        ds = LocalDataset('training')
        task = ds.read_task('c8f0f002')
        assert 'input' in task['test'][0]

    def test_get_all_task_ids(self):
        ds = LocalDataset('training')
        self.assertEqual(len(ds.get_all_task_ids()), 400)
        self.assertIn('c8f0f002', ds.get_all_task_ids())

KaggleDatasetTest().test_get_all_task_ids()
LocalDatasetTest().test_get_all_task_ids()


