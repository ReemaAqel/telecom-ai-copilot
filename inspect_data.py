from pathlib import Path

# مجلد المشروع الذي يحتوي على هذا السكربت
PROJECT_DIR = Path(__file__).resolve().parent

# مجلد مستندات الشركة
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"


def inspect_documents():
    # البحث عن ملفات Markdown
    files = sorted(DOCUMENTS_DIR.glob("*.md"))

    if not files:
        print("No documents found.")
        print(f"Expected folder: {DOCUMENTS_DIR}")
        return

    print(f"Documents found: {len(files)}")

    for file_path in files:
        # قراءة النص العربي بترميز UTF-8
        text = file_path.read_text(encoding="utf-8")

        print("\n" + "=" * 40)
        print(f"File: {file_path.name}")
        print(f"Characters: {len(text)}")
        print(f"Words: {len(text.split())}")
        print(f"Empty: {not bool(text.strip())}")

        print("\nPreview:")
        print(text[:500])


if __name__ == "__main__":
    inspect_documents()