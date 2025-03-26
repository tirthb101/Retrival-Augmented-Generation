import fitz
from docx import Document
import pytesseract
from PIL import Image
import io


def get_full_text(filepath):
    if filepath.split(".")[-1] == "pdf":
        reader = fitz.open(filepath)
        full_text = ""
        count = 1
        for page in reader.pages():
            text = page.get_text()
            if not text.strip():
                pix = page.get_pixmap(dpi=430)
                # pix.save("debug/temp" + str(count) + ".png")
                text = pytesseract.image_to_string(
                    Image.open(io.BytesIO(pix.tobytes("png"))), lang="eng")
            full_text += f"\n\n--- Page {count} ---\n{text}"
            count += 1
    elif filepath.split(".")[-1] == "docx":
        doc = Document(filepath)
        full_text = " ".join([page.text for page in doc.paragraphs])
    else:
        raise Exception("Unsupported File Type")

    with open("debug/text_in_file.txt", "w") as f:
        f.write(full_text)
    return full_text
