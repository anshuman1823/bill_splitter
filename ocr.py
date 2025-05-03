import cv2
import pytesseract
import os
import csv
import regex as re
import numpy as np

def extract_text_from_bill(image):
    """
    Extract text from the passed image using Tesseract OCR.
    """
    # # Convert the PIL image to RGB explicitly
    # image = image.convert("RGB")
    
    # # Convert the PIL image to a NumPy array
    # image_np = np.array(image)

    # Convert RGB to BGR because OpenCV uses BGR format
    bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    _, thresh_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OCR using Tesseract
    extracted_text = pytesseract.image_to_string(thresh_image)

    return extracted_text