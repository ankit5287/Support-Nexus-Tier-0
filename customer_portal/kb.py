# Simulated Knowledge Base (Normally stored in a Vector DB like ChromaDB or Pinecone)

KNOWLEDGE_BASE = [
    {
        "id": 1,
        "title": "How to change my billing date",
        "content": "You can change your billing date by going to Settings > Billing Subscription > Change Date.",
        "category": "Billing"
    },
    {
        "id": 2,
        "title": "I was double charged for my subscription",
        "content": "If you see a double charge, it usually drops in 3 days. If not, submit a ticket for a refund.",
        "category": "Billing"
    },
    {
        "id": 3,
        "title": "How to reset my password",
        "content": "Click 'Forgot Password' on the login screen. We will send an email with a reset link.",
        "category": "Account"
    },
    {
        "id": 4,
        "title": "App keeps crashing on iOS",
        "content": "Please ensure you have iOS 15 or higher. If it still crashes, please submit a Bug Report ticket.",
        "category": "Technical"
    }
]

def mock_vector_search(query):
    """
    In a real final year project, this function would:
    1. Pass `query` into an Embedding Model (e.g., all-MiniLM-L6-v2) to get a vector.
    2. Query a FAISS or ChromaDB index to find vectors with the closest Cosine Similarity.
    
    Here, we do a simple Jaccard similarity simulation for the 'Graceful Fallback'.
    """
    query_words = set(query.lower().split())
    ranked_results = []
    
    for article in KNOWLEDGE_BASE:
        article_words = set(article["title"].lower().split() + article["content"].lower().split())
        # Calculate intersection
        score = len(query_words.intersection(article_words))
        ranked_results.append((score, article))
        
    # Sort by highest score first (simulating Vector proximity ranking)
    ranked_results.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 2 results
    return [res[1] for res in ranked_results[:2] if res[0] > 0]
