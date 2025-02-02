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
        # I = LocalDataset('training').read_task('beb8660c')['train'][0]['input']
        I = LocalDataset('training').read_task('855e0971')['train'][0]['input']
        # I = [[7, 0, 7], [7, 0, 7], [7, 7, 0]] # 007bbfb7
        print(len(I), len(I[0]))
        draw_single_axis(ax, I, draw_edges=False, draw_spine_border=True)
        plt.savefig('image_utils_test_1.png', bbox_inches='tight')

    def test_pil_funcs(self):
        url = "https://storage.googleapis.com/kaggle-organizations/3733/thumbnail.png"
        response = requests.get(url)
        image = Image.open(io.BytesIO(response.content))

        self.assertAlmostEqual(base64_to_pil_image(pil_image_to_base64(image)),image)

if __name__ == '__main__':
    ImageUtilsTest().test_draw_single_axis()
    ImageUtilsTest().test_pil_funcs()