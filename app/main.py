import pdfplumber

def extract_text_from_pdf(file_path):
    results = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(layout=True)
            tables = page.extract_tables()
            results.append({
                "page": i + 1,
                "text": text.strip() if text else "",
                "tables": tables if tables else []
            })
    return results
