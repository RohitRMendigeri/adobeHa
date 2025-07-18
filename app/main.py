import os
import json
from extractor import extract_headings

# Handles both local run and Docker run
INPUT_DIR = "input"
OUTPUT_DIR = "output"
if os.path.exists("/app/input"):
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"

def main():
    print(f"🔍 Checking INPUT_DIR: {INPUT_DIR}")
    
    if not os.path.exists(INPUT_DIR):
        print("❌ Input directory does NOT exist!")
        return
    
    files = os.listdir(INPUT_DIR)
    print(f"📄 Files found: {files}")

    for filename in files:
        print(f"👉 Checking: {filename}")
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"📥 Processing PDF: {filename}")
            try:
                result = extract_headings(pdf_path)
            except Exception as e:
                print(f"❗ Error processing {filename}: {e}")
                continue

            output_filename = filename.replace(".pdf", ".json")
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✅ Saved: {output_path}")
            except Exception as e:
                print(f"❌ Could not save output: {e}")
        else:
            print(f"⛔ Skipping non-PDF: {filename}")

if __name__ == "__main__":
    main()
