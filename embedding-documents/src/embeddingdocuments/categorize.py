# extract_pdf_cpp_simple.py
import fitz  # PyMuPDF
import sys


# -------------------------
# C++ line classification
# -------------------------
def is_cpp_code(line):
    cpp_keywords = [
        "int",
        "float",
        "double",
        "string",
        "for",
        "while",
        "if",
        "else",
        "return",
        "cout",
        "cin",
        "class",
        "struct",
        "enum",
        "friend",
        "public",
        "private",
        "protected",
        "virtual",
    ]
    line_strip = line.strip()

    # Treat #include and using namespace as code
    if line_strip.startswith("#include") or line_strip.startswith("using namespace"):
        return True

    # If line contains a keyword
    if any(k in line_strip for k in cpp_keywords):
        return True

    # If line contains typical C++ symbols
    if any(s in line_strip for s in [";", "{", "}", "(", ")"]):
        return True

    # Empty or purely punctuation lines are ignored
    return False


# -------------------------
# PDF extraction
# -------------------------
def extract_page_text(pdf_path, page_number):
    doc = fitz.open(pdf_path)
    if page_number < 1 or page_number > len(doc):
        print(f"Error: PDF has only {len(doc)} pages.")
        return None
    page = doc[page_number - 1]  # 0-indexed
    return page.get_text("text").strip()


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_pdf_cpp_simple.py <pdf_path> <page_number>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_number = int(sys.argv[2])

    text = extract_page_text(pdf_path, page_number)
    if text:
        lines = [line for line in text.split("\n") if line.strip()]
        code_snippets = []
        definitions = []

        for line in lines:
            if is_cpp_code(line):
                code_snippets.append(line)
            else:
                definitions.append(line)

        print("--- Definitions ---")
        for d in definitions:
            print(d)

        print("\n--- Code Snippets ---")
        for c in code_snippets:
            print(c)
