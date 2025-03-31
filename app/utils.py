import re

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def chunk_text_by_headings(pages):
    chunks = []
    for page in pages:
        lines = page["text"].split("\n")
        current_chunk = {"text": "", "page": page["page"]}
        for line in lines:
            if re.match(r'^\d+\. ', line):  # e.g., "3. Finance Report"
                if current_chunk["text"]:
                    chunks.append(current_chunk)
                current_chunk = {"text": line + "\n", "page": page["page"]}
            else:
                current_chunk["text"] += line + "\n"
        if current_chunk["text"]:
            chunks.append(current_chunk)
    return chunks
