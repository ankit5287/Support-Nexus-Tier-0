import os
import json

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except ImportError:
    print("Please run `pip install sentence-transformers faiss-cpu` to build the Vector DB.")
    exit(1)

def build_vector_database():
    print("🚀 Starting Big Data Vector Knowledge Base Construction...")

    # 1. Load Big Data Corpus
    # In reality, this would be thousands of pages of Docs.
    # We will simulate the corpus here:
    corpus = [
        {"id": 1, "text": "Billing Subscriptions: How to change your billing date and payment method."},
        {"id": 2, "text": "Refunds: I was double charged for my subscription, how do I get my money back?"},
        {"id": 3, "text": "Account Security: How to reset your password and enable 2FA."},
        {"id": 4, "text": "Technical Issues: iOS App keeps crashing on startup when opening images."}
    ]

    # 2. Extract texts to embed
    documents = [doc["text"] for doc in corpus]
    
    # 3. Load Embedding Model
    print("🧠 Loading SentenceTransformer Embedding Model (all-MiniLM-L6-v2) ...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    # 4. Generate High-Dimensional Vector Embeddings
    print(f"🧬 Converting {len(documents)} documents into Semantic Vectors...")
    embeddings = embedder.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')

    # 5. Build FAISS Index (The actual Vector Database)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    
    print("🗄️ Inserting Vectors into FAISS Space...")
    index.add(embeddings)

    # 6. Save the Index to Disk
    os.makedirs("../vector_db", exist_ok=True)
    faiss.write_index(index, "../vector_db/knowledge_base.index")
    
    # Save the id-mapping separately so the Django server can retrieve the text
    with open("../vector_db/corpus_mapping.json", "w") as f:
        json.dump(corpus, f)

    print("✅ Vector Database successfully built and saved to ../vector_db/knowledge_base.index!")

if __name__ == "__main__":
    build_vector_database()
