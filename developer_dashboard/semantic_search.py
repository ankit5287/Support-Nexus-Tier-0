import numpy as np
# Heavy imports moved inside methods to avoid Vercel bootstrap crashes
from customer_portal.models import SupportCase
from django.utils import timezone
import os

# Singleton pattern for the search engine
class SemanticSearchEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticSearchEngine, cls).__new__(cls)
            cls._instance.model = None
            try:
                from sentence_transformers import SentenceTransformer
                cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"[Semantic Engine] Warning: Model unavailable ({e})")
            cls._instance.index = None
            cls._instance.ticket_ids = []
        return cls._instance

    def rebuild_index(self):
        """Builds a FAISS IP index from all existing tickets with L2 normalization."""
        if not self.model: 
            print("[Semantic Engine] Indexing aborted: No model.")
            return

        try:
            import faiss
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
        except Exception as e:
            print(f"[Semantic Engine] Indexing error: {e}")

    def calculate_weighted_score(self, ticket, cosine_similarity):
        """
        High-End Academic Ranking: 
        Score = (Similarity * 0.6) + (Status/Resolved * 0.2) + (Recency * 0.2)
        """
        # 1. Semantic Similarity (60%)
        sim_score = max(0, min(1, float(cosine_similarity)))
        
        # 2. Status/Resolved Boost (20%)
        # Logic: In an academic/audit context, resolved cases are often high-value patterns.
        status_score = 1.0 if ticket.status == 'Resolved' else 0.4
        
        # 3. Recency (20%) - Linear decay over 30 days
        now = timezone.now()
        delta = now - ticket.created_at
        days_old = delta.days + (delta.seconds / 86400)
        recency_score = max(0, 1 - (days_old / 30))
        
        final_score = (sim_score * 0.6) + (status_score * 0.2) + (recency_score * 0.2)
        return final_score

    def search(self, query, top_k=15):
        """Performs weighted semantic search across all domains."""
        if not self.index:
            self.rebuild_index()
            
        if not self.index:
            return []
            
        if not self.model: return []

        try:
            import faiss
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            query_embedding = np.array(query_embedding).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search returns similarities (Inner Product) since we normalized
            similarities, indices = self.index.search(query_embedding, top_k * 2) # Get more to re-rank
        except Exception as e:
            print(f"[Semantic Engine] Search error: {e}")
            return []
        
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
