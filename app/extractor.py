import fitz  # PyMuPDF
import re

# --- Configuration ---
IGNORED_HEADINGS = [
    "Acknowledgements", "Revision History", "Table of Contents",
    "Version", "Copyright Notice"
]

# --- Helper functions ---

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())

def is_useful_heading(text):
    if not text or len(text) < 3:
        return False
    if any(skip.lower() in text.lower() for skip in IGNORED_HEADINGS):
        return False
    return True

def classify_by_pattern(text):
    """
    Classifies heading level using regex patterns like:
    - 1.               => H1
    - 1.1 or 1.2.3     => H2 or H3 depending on depth
    """
    pattern = re.match(r'^(\d+(\.\d+){0,2})', text)
    if pattern:
        levels = pattern.group(0).count('.')
        if levels == 0:
            return "H1"
        elif levels == 1:
            return "H2"
        else:
            return "H3"
    return None

# --- Main function ---

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)
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
            if not is_useful_heading(merged_text):
                continue

            avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0

            blocks.append({
                "text": merged_text,
                "size": avg_size,
                "page": page_num
            })

    if not blocks:
        return {
            "title": "Untitled Document",
            "outline": []
        }

    # Sort by size to guess title
    blocks.sort(key=lambda b: -b["size"])
    title = blocks[0]["text"]

    # Font-size based level (fallback)
    size_ranks = sorted(list(set(b["size"] for b in blocks)), reverse=True)
    size_to_level = {}
    for i, size in enumerate(size_ranks[:3]):
        size_to_level[size] = f"H{i+1}"

    # Final heading classification
    seen = set()
    headings = []

    for block in blocks:
        text = block["text"]
        page = block["page"]
        size = block["size"]

        if text in seen:
            continue
        seen.add(text)

        # Prefer pattern classification
        level = classify_by_pattern(text)

        # Fallback: use font size
        if not level:
            level = size_to_level.get(size, None)

        if not level:
            continue

        headings.append({
            "level": level,
            "text": text,
            "page": page
        })

    return {
        "title": title,
        "outline": headings
    }
