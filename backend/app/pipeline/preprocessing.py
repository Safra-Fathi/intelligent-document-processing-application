import cv2
import numpy as np
from PIL import Image


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Prepare an image for OCR.

    Steps:
    1. Convert the image to grayscale.
    2. Reduce image noise.
    3. Apply adaptive thresholding to improve text visibility.
    """

    # Convert PIL image to a NumPy array
    image_array = np.array(image.convert("RGB"))

    # Convert RGB image to grayscale
    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY,
    )

    # Reduce small amounts of image noise
    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # Improve text/background separation
    thresholded = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    return Image.fromarray(thresholded)