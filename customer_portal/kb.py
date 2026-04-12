import numpy as np
import os

# Simulated Knowledge Base (Normally stored in a Vector DB like ChromaDB or Pinecone)
KNOWLEDGE_BASE = [
    {
        "id": 1,
        "title": "Changing Nexus ID Billing Date",
        "content": "Access your Nexus IDs settings, select Quantum Wallet, and choose 'Reschedule Billing' to modify your payment cycle.",
        "category": "Billing"
    },
    {
        "id": 2,
        "title": "Quantum Pro: Neural Double Charges",
        "content": "Duplicate pending charges on your Nexus Quantum Pro are usually authorization holds. They reconcile automatically within 48 hours.",
        "category": "Billing"
    },
    {
        "id": 3,
        "title": "Nexus ID Security: Biometric Resets",
        "content": "To reset your biometric Nexus ID, use a secondary verified device or visit the Nexus Recovery portal.",
        "category": "Account"
    },
    {
        "id": 4,
        "title": "Quantum Smartphone: App Stability",
        "content": "If NexusOS apps crash, ensure you are on the latest Neural Engine firmware (v2.4+). Reset the app cache in System Settings.",
        "category": "Technical"
    }
]

# --- Attempt to load real semantic search model ---
SEMANTIC_SEARCH_AVAILABLE = False
_model = None
_kb_embeddings = None

try:
    from sentence_transformers import SentenceTransformer, util
    print("Initializing Nexus Neural embedding model...")
    _model = SentenceTransformer('all-MiniLM-L6-v2')
    kb_texts = [f"{a['title']} {a['content']}" for a in KNOWLEDGE_BASE]
    _kb_embeddings = _model.encode(kb_texts, convert_to_tensor=True)
    SEMANTIC_SEARCH_AVAILABLE = True
    print("Nexus Neural KB Search: Ready (Semantic Mode).")
except ImportError:
    print("WARNING: 'sentence_transformers' not installed. KB Search will use keyword fallback mode.")
except Exception as e:
    print(f"WARNING: Could not load sentence_transformers model: {e}. Using keyword fallback.")


def _keyword_search(query):
    """
    Fallback: Simple keyword-based search when semantic model is unavailable.
    Matches query words against KB titles and content.
    """
    query_words = set(query.lower().split())
    scored = []
    for article in KNOWLEDGE_BASE:
        combined = f"{article['title']} {article['content']}".lower()
        score = sum(1 for word in query_words if word in combined)
        if score > 0:
            scored.append((score, article))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [res[1] for res in scored[:2]]


def mock_vector_search(query):
    """
    Advanced Neural Search (Pillar 6: Embedding based semantic search):
    1. If sentence_transformers is available: encodes query into a 384-dimensional vector
       and performs Cosine Similarity ranking against the KB index.
    2. Fallback: keyword-based matching when the model is not installed.
    Returns top results ranked by Semantic Relevance.
    """
    if SEMANTIC_SEARCH_AVAILABLE and _model is not None and _kb_embeddings is not None:
        # Real semantic search
        from sentence_transformers import util
        query_embedding = _model.encode(query, convert_to_tensor=True)
        cosine_scores = util.cos_sim(query_embedding, _kb_embeddings)[0]

        ranked_results = []
        for i, score in enumerate(cosine_scores):
            ranked_results.append((score.item(), KNOWLEDGE_BASE[i]))

        ranked_results.sort(key=lambda x: x[0], reverse=True)
        return [res[1] for res in ranked_results[:2] if res[0] > 0.35]
    else:
        # Keyword fallback
        return _keyword_search(query)
