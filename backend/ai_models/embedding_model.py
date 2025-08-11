import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """Multilingual embedding model for RAG system"""
    
    def __init__(self, model_name: str = "intfloat/multilingual-E5-large"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 1024  # E5-large dimension
        
    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for text"""
        # Add E5 prefix for better performance
        if isinstance(text, str):
            text = f"query: {text}"  # For queries
        
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    async def embed_documents(self, documents: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple documents"""
        # Add E5 prefix for documents
        docs_with_prefix = [f"passage: {doc}" for doc in documents]
        embeddings = self.model.encode(docs_with_prefix, normalize_embeddings=True)
        return embeddings