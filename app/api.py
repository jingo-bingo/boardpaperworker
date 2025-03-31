from fastapi import FastAPI, UploadFile, File
from main import extract_text_from_pdf
from utils import clean_text, chunk_text_by_headings
import tempfile

app = FastAPI()

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    raw = extract_text_from_pdf(tmp_path)
    for page in raw:
        page["text"] = clean_text(page["text"])
    chunks = chunk_text_by_headings(raw)

    return {
        "pages": len(raw),
        "chunks": chunks[:5],  # preview only first 5
        "status": "ok"
    }
