from fastapi import FastAPI, UploadFile, File
from main import extract_text_from_pdf
from utils import clean_text, chunk_text_by_headings
import tempfile


from supabase import create_client
import os
import requests
from datetime import datetime
from utils import (
    clean_text,
    chunk_text_by_headings,
    determine_chunk_type,
    extract_section_title,
    extract_title,
    calculate_word_count,
    calculate_reading_time
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

@app.post("/process-from-supabase/")
def process_from_supabase(payload: dict):
    document_id = payload.get("document_id")
    if not document_id:
        return {"error": "Missing document_id"}

    # 1. Get file name from Supabase DB
    doc = supabase.table("board_documents").select("*").eq("id", document_id).single().execute().data
    file_name = doc["file_name"]

    # 2. Generate signed URL to download the file
    storage_url = supabase.storage.from_("boardpapers").create_signed_url(file_name, 600)["signedURL"]

    # 3. Download PDF to temp file
    response = requests.get(storage_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        file_path = tmp.name

    # 4. Extract + clean + chunk
    raw = extract_text_from_pdf(file_path)
    transformed_chunks = []

    for page_data in raw:
        page_data["text"] = clean_text(page_data["text"])
        page_chunks = chunk_text_by_headings([page_data])

        for i, chunk in enumerate(page_chunks):
            transformed_chunks.append({
                "document_id": document_id,
                "index": i,
                "content": chunk["text"],
                "type": determine_chunk_type(chunk["text"]),
                "pageNumber": chunk["page"],
                "sectionTitle": extract_section_title(chunk["text"])
            })

    # 5. Insert chunks into Supabase
    for chunk in transformed_chunks:
        supabase.table("document_chunks").insert(chunk).execute()

    # 6. Insert metadata
    metadata = {
        "document_id": document_id,
        "title": extract_title(raw),
        "numPages": len(raw),
        "processingStage": "complete",
        "processingDate": datetime.utcnow().isoformat(),
        "wordCount": calculate_word_count(raw),
        "estimatedReadingTime": calculate_reading_time(raw)
    }

    supabase.table("document_metadata").upsert(metadata).execute()

    return {
        "status": "success",
        "chunks_added": len(transformed_chunks),
        "pages": len(raw)
    }
