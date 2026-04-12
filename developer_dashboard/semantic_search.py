import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import faiss
from customer_portal.models import SupportCase
from django.utils import timezone
import os

# Singleton pattern for the search engine
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
        """Builds a FAISS IP index from all existing tickets with L2 normalization."""
        tickets = SupportCase.objects.all()
        if not tickets.exists():
            return
            
        texts = [t.ticket_text for t in tickets]
        self.ticket_ids = [t.id for t in tickets]
        
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # L2 Normalization for Cosine Similarity
        faiss.normalize_L2(embeddings)
        
        # Using IndexFlatIP for Inner Product (Cosine Similarity if normalized)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def calculate_weighted_score(self, ticket, cosine_similarity):
        """
        Score = (Similarity * 0.6) + (Recency * 0.2) + (Priority/Status * 0.2)
        """
        # 1. Similarity (0 to 1)
        sim_score = max(0, min(1, float(cosine_similarity)))
        
        # 2. Recency (0 to 1) - Linear decay over 30 days
        now = timezone.now()
        delta = now - ticket.created_at
        days_old = delta.days + (delta.seconds / 86400)
        recency_score = max(0, 1 - (days_old / 30))
        
        # 3. Status/Priority Weight (0 to 1)
        # Resolved = 1.0, Escalated = 0.8, In Progress = 0.5, Open = 0.2
        status_weights = {
            'Resolved': 1.0,
            'Escalated': 0.8,
            'In Progress': 0.5,
            'Open': 0.2
        }
        status_score = status_weights.get(ticket.status, 0.2)
        
        final_score = (sim_score * 0.6) + (recency_score * 0.2) + (status_score * 0.2)
        return final_score

    def search(self, query, top_k=15):
        """Performs weighted semantic search across all domains."""
        if not self.index:
            self.rebuild_index()
            
        if not self.index:
            return []
            
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search returns similarities (Inner Product) since we normalized
        similarities, indices = self.index.search(query_embedding, top_k * 2) # Get more to re-rank
        
        scored_results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: continue
            ticket_id = self.ticket_ids[idx]
            sim = similarities[0][i]
            
            try:
                ticket = SupportCase.objects.get(id=ticket_id)
                score = self.calculate_weighted_score(ticket, sim)
                scored_results.append((ticket, score))
            except SupportCase.DoesNotExist:
                continue
        
        # Sort by final weighted score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [res[0] for res in scored_results[:top_k]]

# Convenience function
def semantic_ticket_query(query_text):
    engine = SemanticSearchEngine()
    return engine.search(query_text)
