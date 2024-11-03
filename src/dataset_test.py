from pathlib import Path
from unittest import TestCase

from dataset import KaggleDataset


class KaggleDatasetTest(TestCase):

    def test_read_task(self):
        ds = KaggleDataset("arc-agi_training_challenges.json", Path("../data/kaggle") )
        task = ds.read_task("c8f0f002")
        assert "input" in task['test'][0]

