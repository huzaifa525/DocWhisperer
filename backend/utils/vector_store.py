from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.embedder = SentenceTransformer(model_name)
        self.reset()

    def reset(self):
        self.documents = []
        self.embeddings = np.array([])
        self.chunks = []

    def add_document(self, document, chunk_size: int = 500, overlap: int = 50) -> bool:
        new_chunks = self._chunk_text(document.content, chunk_size, overlap)
        if not new_chunks:
            return False

        new_embeddings = self.embedder.encode(new_chunks)
        
        document.chunks = new_chunks
        document.embeddings = new_embeddings
        
        self.documents.append(document)
        self.chunks.extend(new_chunks)
        
        if self.embeddings.size == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        return True

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text = text.strip()
        
        while start < len(text):
            end = start + chunk_size
            
            if end > len(text):
                end = len(text)
            else:
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_period, last_newline)
                
                if break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start += chunk_size - overlap
        
        return chunks

    def search(self, query: str, k: int = 3) -> List[str]:
        if not self.chunks or len(self.chunks) == 0:
            return []
            
        query_embedding = self.embedder.encode([query])[0]
        
        if self.embeddings.size == 0:
            return []
            
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        return [self.chunks[i] for i in top_k_indices]