import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"
OUTPUT_PATH = PROJECT_DIR / "data" / "chunks.json"


def split_document(file_path: Path) -> list[dict]:
    """تقسيم مستند Markdown حسب عناوين المستوى الثاني."""

    text = file_path.read_text(encoding="utf-8")

    document_title = file_path.stem
    section_title = "Introduction"
    section_lines = []
    chunks = []

    def save_section():
        content = "\n".join(section_lines).strip()

        # لا نحفظ الأقسام الفارغة
        if not content:
            return

        chunks.append({
            "chunk_id": f"{file_path.stem}_{len(chunks) + 1:03d}",
            "source": file_path.name,
            "document_title": document_title,
            "section_title": section_title,
            "text": (
                f"{document_title}\n"
                f"{section_title}\n"
                f"{content}"
            ),
        })

    for line in text.splitlines():
        if line.startswith("# "):
            document_title = line[2:].strip()

        elif line.startswith("## "):
            # حفظ محتوى القسم السابق قبل بدء القسم الجديد
            save_section()

            section_title = line[3:].strip()
            section_lines = []

        else:
            section_lines.append(line)

    # حفظ آخر قسم؛ لأنه لا يوجد عنوان بعده ليحفّز الحفظ
    save_section()

    return chunks


def prepare_documents():
    files = sorted(DOCUMENTS_DIR.glob("*.md"))

    if not files:
        raise FileNotFoundError(
            f"No Markdown documents found in: {DOCUMENTS_DIR}"
        )

    all_chunks = []

    for file_path in files:
        document_chunks = split_document(file_path)
        all_chunks.extend(document_chunks)

        print(f"{file_path.name}: {len(document_chunks)} chunks")

    if not all_chunks:
        raise ValueError("The documents contain no usable text.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nFirst chunk:")
    print(json.dumps(all_chunks[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    prepare_documents()