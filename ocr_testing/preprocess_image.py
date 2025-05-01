import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pillow_heif
import easyocr
import os

def convert_heic_to_jpg(heic_path, output_jpg_path=None):
    heif_file = pillow_heif.read_heif(heic_path)
    image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
    
    if output_jpg_path is None:
        output_jpg_path = heic_path.rsplit('.', 1)[0] + '.jpg'
    image.save(output_jpg_path, "JPEG")
    return output_jpg_path

def enhance_image(image_path):
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance

    # Load and enhance
    image = Image.open(image_path)
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = ImageEnhance.Sharpness(image).enhance(2.0)

    # Resize for consistency
    base_width = 1200
    w_percent = base_width / float(image.size[0])
    h_size = int(float(image.size[1]) * w_percent)
    image = image.resize((base_width, h_size), Image.LANCZOS)

    # Convert to grayscale OpenCV format
    img_np = np.array(image)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Slightly stronger bilateral filter for background smoothing
    filtered = cv2.bilateralFilter(gray, d=11, sigmaColor=95, sigmaSpace=95)

    # More aggressive contrast stretching (shift percentile)
    min_val, max_val = np.percentile(filtered, (10, 90))  # increased from 5–95
    stretched = np.clip((filtered - min_val) * 255.0 / (max_val - min_val), 0, 255).astype(np.uint8)

    # Threshold (Otsu)
    _, binary = cv2.threshold(stretched, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save processed image
    processed_path = image_path.rsplit('.', 1)[0] + '_ocr_ready.jpg'
    cv2.imwrite(processed_path, binary)

    return processed_path

def extract_text_easyocr(image_path, lang='en'):
    reader = easyocr.Reader([lang])
    results = reader.readtext(image_path)
    return results

def run_ocr_pipeline(heic_path):
    print(f"📥 Converting HEIC → JPG: {heic_path}")
    jpg_path = convert_heic_to_jpg(heic_path)

    # print("🎨 Enhancing image for OCR...")
    # processed_path = enhance_image(jpg_path)

    # print("🔍 Running OCR with EasyOCR...")
    # results = extract_text_easyocr(processed_path)
    results = extract_text_easyocr(jpg_path)

    print("\n📝 Detected Text:\n")
    for bbox, text, confidence in results:
        print(f"[{confidence:.2f}] {text}")

# 🔧 Example usage
if __name__ == "__main__":
    image_path = os.path.join(os.getcwd(), "bills_image", "bill_1.heic")
    heic_image_path = image_path  # Replace with your file path
    run_ocr_pipeline(heic_image_path)