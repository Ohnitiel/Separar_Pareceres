import cv2
import numpy as np

from PIL import Image
from deskew import determine_skew
from skimage.color import rgb2gray
from skimage.transform import rotate

def unskewImg(image):
    image = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    grayscale = rgb2gray(image)
    angle = determine_skew(grayscale)
    rotated = rotate(image, angle, resize=True) * 255
    return Image.fromarray(rotated.astype(np.uint8))