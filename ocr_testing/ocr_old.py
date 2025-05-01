import cv2
import pytesseract
import os
import csv
import regex as re

def process_image_for_ocr(image_path):
    """
    Load an image from the given path, preprocess it, and extract text using Tesseract OCR.
    Saves the text to a csv file if the text matches a bill format
    """
    
    cwd = os.getcwd()  # Get the current working directory (cwd)

    def extract_text_from_bill(image_path):
        """
        Load an image from the given path, preprocess it, and extract text using Tesseract OCR.
        """
        # Load the image using OpenCV
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Unable to load image at path '{image_path}'")
            return None

        # Convert the image from BGR (OpenCV default) to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert to grayscale to simplify the image data
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

        # Apply thresholding (you can adjust the threshold values if needed)
        ret, thresh_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Use Tesseract OCR to extract text from the preprocessed image
        extracted_text = pytesseract.image_to_string(thresh_image)
        return extracted_text

    def get_supermarket(text):
        for supermarket in supermarkets_list:
            if supermarket in text.lower():
                return supermarket
        return None

    
    text = extract_text_from_bill(image_path)

    supermarkets_list = ["tesco", "asda", "sainsbury", "morrisons", "aldi", "lidl", "waitrose", "m&s"]
    supermarket_name = get_supermarket(text)
    print(f"Supermarket Name Detected: {supermarket_name}")

    # Regex pattern to match item names and prices
    aldi_pattern = r"^\d+\s+([A-Z0-9\s]+?)\s+(\d+\.\d{2})"

    # function to recognize if a text line is a valid bill entry
    def is_bill_entry(line):
        return re.match(aldi_pattern, line) # regex acc to Aldi bills

    # function to extract bill items from the text and save it to a csv file
    def csv_bill(text):
        # Extracting the bill items
        bill_items = []
        for line in text.split("\n"):
            if line.strip() == "":
                continue
            if is_bill_entry(line):
                line_txt = re.search(aldi_pattern, line).group(0)
                line_txt = line_txt.split(" ")
                # print(line_txt)
                line_txt = [supermarket_name, line_txt[0], " ".join(line_txt[1:-1]), line_txt[-1]]
                bill_items.append(line_txt)
        
        bill_csv_path = os.path.join(cwd, "bills_output", "bill_items.csv")
        
        with open(bill_csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(bill_items)

    if text is not None:
        # Save the extracted text to a file
        ocr_output_text_path = os.path.join(cwd, "bills_output", "extracted_text.txt")
        with open(ocr_output_text_path, "w") as file:
            file.write(text)

        csv_bill(text) # save bill items to a csv file


bill_image_path = os.path.join(os.getcwd(), "bills_image", "ss.png")
process_image_for_ocr(bill_image_path)