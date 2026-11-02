import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = PROJECT_DIR / "data" / "chunks.json"

MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


class DocumentSearch:
    def __init__(self):
        if not CHUNKS_PATH.is_file():
            raise FileNotFoundError(
                "Run prepare_documents.py first."
            )

        # قراءة المقاطع المحفوظة
        self.chunks = json.loads(
            CHUNKS_PATH.read_text(encoding="utf-8")
        )

        if not self.chunks:
            raise ValueError("The chunks file is empty.")

        # تحميل نموذج Embeddings جاهز
        print("Loading embedding model...")

        self.model = SentenceTransformer(
            MODEL_NAME,
            device="cpu",
        )

        # استخراج نص كل مقطع
        texts = [chunk["text"] for chunk in self.chunks]

        # تحويل النصوص إلى متجهات
        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        print(f"Chunks loaded: {len(self.chunks)}")
        print(f"Embeddings shape: {self.embeddings.shape}")

    def search(self, question: str, top_k: int = 3) -> list[dict]:
        question = question.strip()

        if not question:
            raise ValueError("The question cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        # تحويل السؤال بنفس نموذج المقاطع
        question_embedding = self.model.encode(
            question,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        # مع المتجهات المطبّعة، الضرب النقطي يعطي cosine similarity
        scores = self.embeddings @ question_embedding

        # ترتيب مواقع المقاطع من الأعلى تشابهًا إلى الأقل
        best_indices = np.argsort(-scores)[:top_k]

        results = []

        for index in best_indices:
            chunk = self.chunks[int(index)]

            results.append({
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "section_title": chunk["section_title"],
                "text": chunk["text"],
                "score": float(scores[index]),
            })

        return results


if __name__ == "__main__":
    search_engine = DocumentSearch()

    while True:
        question = input("\nAsk a question, or type exit: ")

        if question.strip().lower() == "exit":
            break

        if not question.strip():
            print("Please enter a question.")
            continue

        results = search_engine.search(question)

        for rank, result in enumerate(results, start=1):
            print("\n" + "=" * 50)
            print(f"Rank: {rank}")
            print(f"Source: {result['source']}")
            print(f"Section: {result['section_title']}")
            print(f"Similarity: {result['score']:.3f}")
            print(result["text"])