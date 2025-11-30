import fitz  # PyMuPDF
import os
import sys


def extract_images(pdf_path, output_folder="images", page_number=None):
    """
    Extract images from a PDF.
    - pdf_path: path to PDF file
    - output_folder: folder to save extracted images
    - page_number: optional, extract only a specific page (1-indexed)
    """
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = [doc[page_number - 1]] if page_number else doc  # select page if specified
    img_count = 0

    for i, page in enumerate(pages):
        image_list = page.get_images(full=True)
        print(f"[Page {i+1}] {len(image_list)} images found")
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_name = f"{output_folder}/page{i+1}_img{img_index+1}.{image_ext}"
            with open(image_name, "wb") as f:
                f.write(image_bytes)
            img_count += 1
    print(f"Total images extracted: {img_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_images.py <pdf_path> [page_number]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_number = int(sys.argv[2]) if len(sys.argv) == 3 else None
    extract_images(pdf_path, page_number=page_number)
