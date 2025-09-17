import os
import boto3
from typing import Dict, List, Any, Optional
from pydantic import Field
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.tools import BaseTool
from langchain.schema import Document


class RAGKnowledgeBaseTool(BaseTool):
    """Tool for retrieving information from a knowledge base using RAG."""
    
    name: str = "rag_kb"
    description: str = "Useful for retrieving information from the knowledge base about financial services, banking, and agriculture in Vietnam."
    return_direct: bool = False
    
    # Define fields for Pydantic v2 compatibility
    vector_store_bucket: str = Field(default="agrinfihub-vector-bucket", description="The S3 bucket name where vector indices are stored")
    embedding_model_name: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", description="The HuggingFace model to use for embeddings")
    
    # Fields for non-serializable attributes
    s3_client: Any = Field(default=None, exclude=True)
    embedding_model: Any = Field(default=None, exclude=True)
    vector_stores: Dict = Field(default_factory=dict, exclude=True)
    available_indices: List[str] = Field(default_factory=lambda: ["bank", "financial_news", "government"], exclude=True)
    
    # Pydantic v2 configuration
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"  # Allow extra attributes
    }
    
    def __init__(self, vector_store_bucket: str = "agrinfihub-vector-bucket", 
                 embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", **kwargs):
        """Initialize the RAG knowledge base tool.
        
        Args:
            vector_store_bucket: The S3 bucket name where vector indices are stored
            embedding_model: The HuggingFace model to use for embeddings
        """
        # Initialize parent class with proper field values
        super().__init__(
            vector_store_bucket=vector_store_bucket,
            embedding_model_name=embedding_model,
            **kwargs
        )
        
        # Set up non-serializable attributes after parent initialization  
        self.s3_client = boto3.client('s3')
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vector_stores = {}
        self.available_indices = ["bank", "financial_news", "government"]
    
    def _run(self, query: str, indices: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
        """Run the tool to retrieve information from the knowledge base.
        
        Args:
            query: The query to search for
            indices: List of indices to search in (default: all available indices)
            top_k: Number of results to return per index
            
        Returns:
            Dictionary with search results and metadata
        """
        if not indices:
            indices = self.available_indices
        else:
            # Validate indices
            for idx in indices:
                if idx not in self.available_indices:
                    raise ValueError(f"Invalid index: {idx}. Available indices: {self.available_indices}")
        
        results = {}
        for index_name in indices:
            # Load or get vector store for this index
            vector_store = self._get_vector_store(index_name)
            
            # Search the vector store
            docs = vector_store.similarity_search(query, k=top_k)
            
            # Format results
            results[index_name] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Unknown")
                }
                for doc in docs
            ]
        
        return {
            "query": query,
            "results": results,
            "indices_searched": indices
        }
    
    async def _arun(self, query: str, indices: Optional[List[str]] = None, top_k: int = 5) -> Dict[str, Any]:
        """Async version of _run."""
        # For simplicity, we're just calling the sync version
        return self._run(query, indices, top_k)
    
    def _get_vector_store(self, index_name: str) -> FAISS:
        """Get or load a vector store for the given index.
        
        Args:
            index_name: The name of the index to load
            
        Returns:
            FAISS vector store
        """
        if index_name in self.vector_stores:
            return self.vector_stores[index_name]
        
        # Download the index from S3 if it exists
        local_index_path = f"/tmp/{index_name}_index"
        os.makedirs(local_index_path, exist_ok=True)
        
        try:
            # List objects in the index directory
            response = self.s3_client.list_objects_v2(
                Bucket=self.vector_store_bucket,
                Prefix=f"{index_name}/"
            )
            
            # Download all files for this index
            for obj in response.get('Contents', []):
                file_key = obj['Key']
                local_file = os.path.join(local_index_path, os.path.basename(file_key))
                self.s3_client.download_file(self.vector_store_bucket, file_key, local_file)
            
            # Load the vector store
            vector_store = FAISS.load_local(local_index_path, self.embedding_model)
            self.vector_stores[index_name] = vector_store
            return vector_store
            
        except Exception as e:
            # If there's an error, create a dummy vector store with a warning message
            dummy_doc = Document(
                page_content=f"Error loading index {index_name}: {str(e)}",
                metadata={"source": "error", "index": index_name}
            )
            vector_store = FAISS.from_documents([dummy_doc], self.embedding_model)
            self.vector_stores[index_name] = vector_store
            return vector_store