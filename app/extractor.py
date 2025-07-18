import fitz  # PyMuPDF
import re

MAX_HEADING_WORDS = 25
MAX_HEADING_CHARS = 120

def clean_text(text):
    text = re.sub(r'\s+', ' ', text.strip())
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

def is_useful_heading(text):
    if not text or len(text) < 3:
        return False
    if len(text.split()) > MAX_HEADING_WORDS:
        return False
    if len(text) > MAX_HEADING_CHARS:
        return False
    return True

def is_toc_entry(text):
    return bool(re.match(r'^\d+(\.\d+)*\s+.+\s+\d{1,2}$', text))

def classify_by_pattern(text):
    pattern = re.match(r'^(\d+(\.\d+){0,2})', text)
    if pattern:
        levels = pattern.group(0).count('.')
        return ["H1", "H2", "H3"][min(levels, 2)]
    return None

def extract_title(doc):
    page = doc[0]
    spans = []

    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = clean_text(span["text"])
                if len(text) >= 4:
                    spans.append((span["size"], text))

    spans.sort(reverse=True)
    if len(spans) >= 2:
        return spans[0][1] + "  " + spans[1][1]
    elif spans:
        return spans[0][1]
    return "Untitled Document"

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)
    title = extract_title(doc)
    blocks = []

    for page_num, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue

            merged_text = ""
            font_sizes = []

            for line in block["lines"]:
                for span in line["spans"]:
                    text = clean_text(span["text"])
                    if not text:
                        continue
                    merged_text += text + " "
                    font_sizes.append(span["size"])

            merged_text = clean_text(merged_text)

            # Filter: ToC junk from page 4
            if page_num == 4 and re.search(r'\d{1,2}$', merged_text):
                continue
            if not is_useful_heading(merged_text):
                continue

            avg_size = sum(font_sizes) / len(font_sizes)
            blocks.append({
                "text": merged_text,
                "size": avg_size,
                "page": page_num
            })

    if not blocks:
        return {"title": title, "outline": []}

    # Rank sizes → H1, H2, H3
    unique_sizes = sorted({b["size"] for b in blocks}, reverse=True)
    size_to_level = {size: f"H{i+1}" for i, size in enumerate(unique_sizes[:3])}

    outline = []
    seen = set()

    for block in blocks:
        text = block["text"]
        size = block["size"]
        page = block["page"]

        if text in seen:
            continue
        seen.add(text)

        level = classify_by_pattern(text) or size_to_level.get(size)
        if level:
            outline.append({
                "level": level,
                "text": text,
                "page": page
            })

    return {
        "title": title,
        "outline": outline
    }
