import io
import unittest
from matplotlib import pyplot as plt
from PIL import Image
import requests


from dataset import LocalDataset
from image_utils import base64_to_pil_image, draw_single_axis, pil_image_to_base64

class ImageUtilsTest(unittest.TestCase):
    def test_draw_single_axis(self):
        fig, ax = plt.subplots()
        I = LocalDataset('training').read_task('beb8660c')['train'][0]['input']
        draw_single_axis(ax, I, draw_edges=False, draw_spine_border=True)
        plt.savefig('image_utils_test_1.png', bbox_inches='tight')

    def test_pil_funcs(self):
        url = "https://storage.googleapis.com/kaggle-organizations/3733/thumbnail.png"
        response = requests.get(url)
        image = Image.open(io.BytesIO(response.content))

        self.assertAlmostEqual(base64_to_pil_image(pil_image_to_base64(image)),image)