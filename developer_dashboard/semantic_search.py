import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import faiss
from customer_portal.models import SupportCase
import os

# Singleton pattern for the search engine to avoid re-loading the model
class SemanticSearchEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticSearchEngine, cls).__new__(cls)
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2')
            cls._instance.index = None
            cls._instance.ticket_ids = []
        return cls._instance

    def rebuild_index(self):
        """Builds a FAISS index from all existing tickets."""
        tickets = SupportCase.objects.all()
        if not tickets.exists():
            return
            
        texts = [t.ticket_text for t in tickets]
        self.ticket_ids = [t.id for t in tickets]
        
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        embeddings = np.array(embeddings).astype('float32')
        
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query, top_k=10):
        """Performs semantic search across all domains."""
        if not self.index:
            self.rebuild_index()
            
        if not self.index:
            return []
            
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx in indices[0]:
            if idx == -1: continue
            ticket_id = self.ticket_ids[idx]
            try:
                ticket = SupportCase.objects.get(id=ticket_id)
                results.append(ticket)
            except SupportCase.DoesNotExist:
                continue
        return results

# Convenience function
def semantic_ticket_query(query_text):
    engine = SemanticSearchEngine()
    return engine.search(query_text)
