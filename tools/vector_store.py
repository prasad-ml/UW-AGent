"""
Vector store implementation using ChromaDB for policy document storage and retrieval.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from pathlib import Path
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config import settings

logger = logging.getLogger(__name__)


class PolicyVectorStore:
    """
    Manages policy documents in ChromaDB for semantic search and retrieval.
    """
    
    def __init__(self, persist_directory: Optional[str] = None, collection_name: Optional[str] = None):
        """
        Initialize the PolicyVectorStore.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        self.embeddings = None
        
        logger.info(f"PolicyVectorStore initialized with persist_directory: {self.persist_directory}")
    
    def initialize_db(self) -> None:
        """
        Initialize ChromaDB with persistent storage and embeddings.
        """
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model="text-embedding-3-small"
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Underwriting policy documents"}
            )
            
            logger.info(f"ChromaDB initialized successfully. Collection: {self.collection_name}")
            logger.info(f"Collection contains {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def _split_policy_text(self, text: str) -> List[str]:
        """
        Split policy text into chunks for better embedding and retrieval.
        
        Args:
            text: Policy text to split
            
        Returns:
            List of text chunks
        """
        # Split by policy sections (REVIEW_RULE markers)
        policies = []
        current_policy = []
        
        for line in text.split('\n'):
            if line.startswith('REVIEW_RULE:') and current_policy:
                # Save previous policy
                policies.append('\n'.join(current_policy))
                current_policy = [line]
            else:
                current_policy.append(line)
        
        # Add the last policy
        if current_policy:
            policies.append('\n'.join(current_policy))
        
        # Further split if policies are too large
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        
        final_chunks = []
        for policy in policies:
            if len(policy) > 1000:
                chunks = text_splitter.split_text(policy)
                final_chunks.extend(chunks)
            else:
                final_chunks.append(policy)
        
        return [chunk.strip() for chunk in final_chunks if chunk.strip()]
    
    def _generate_doc_id(self, text: str) -> str:
        """
        Generate a unique ID for a document based on its content.
        
        Args:
            text: Document text
            
        Returns:
            Unique document ID
        """
        return hashlib.md5(text.encode()).hexdigest()
    
    def load_policies(self, policy_texts: List[str]) -> Dict:
        """
        Embed and store policy documents in ChromaDB.
        
        Args:
            policy_texts: List of policy document texts
            
        Returns:
            Dictionary with loading statistics
        """
        if not self.collection:
            raise RuntimeError("Database not initialized. Call initialize_db() first.")
        
        logger.info(f"Loading {len(policy_texts)} policy documents...")
        
        all_chunks = []
        all_ids = []
        all_metadatas = []
        
        for idx, policy_text in enumerate(policy_texts):
            # Split policy into chunks
            chunks = self._split_policy_text(policy_text)
            
            # Extract review rule name if present
            review_rule = "UNKNOWN"
            for line in policy_text.split('\n'):
                if line.startswith('REVIEW_RULE:'):
                    review_rule = line.replace('REVIEW_RULE:', '').strip()
                    break
            
            for chunk_idx, chunk in enumerate(chunks):
                # Generate unique ID
                doc_id = self._generate_doc_id(f"{idx}_{chunk_idx}_{chunk}")
                
                # Create metadata
                metadata = {
                    "policy_index": idx,
                    "chunk_index": chunk_idx,
                    "review_rule": review_rule,
                    "source": "sample_policies.txt"
                }
                
                all_chunks.append(chunk)
                all_ids.append(doc_id)
                all_metadatas.append(metadata)
        
        # Generate embeddings and add to collection
        try:
            embeddings_list = self.embeddings.embed_documents(all_chunks)
            
            # Add to ChromaDB
            self.collection.add(
                documents=all_chunks,
                embeddings=embeddings_list,
                metadatas=all_metadatas,
                ids=all_ids
            )
            
            stats = {
                "total_policies": len(policy_texts),
                "total_chunks": len(all_chunks),
                "collection_count": self.collection.count()
            }
            
            logger.info(f"Successfully loaded policies: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error loading policies: {e}")
            raise
    
    def load_policies_from_file(self, filepath: str) -> Dict:
        """
        Load policies from a text file.
        
        Args:
            filepath: Path to the policy file
            
        Returns:
            Dictionary with loading statistics
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into individual policies by REVIEW_RULE markers
            policy_texts = []
            current_policy = []
            
            for line in content.split('\n'):
                if line.startswith('REVIEW_RULE:') and current_policy:
                    # Save previous policy
                    policy_texts.append('\n'.join(current_policy))
                    current_policy = [line]
                else:
                    current_policy.append(line)
            
            # Add the last policy
            if current_policy:
                policy_texts.append('\n'.join(current_policy))
            
            logger.info(f"Split file into {len(policy_texts)} separate policies")
            
            return self.load_policies(policy_texts)
            
        except Exception as e:
            logger.error(f"Error loading policies from file {filepath}: {e}")
            raise
    
    def query_policy(self, review_rule: str, top_k: int = 3) -> List[Dict]:
        """
        Query relevant policy sections based on review rule.
        
        Args:
            review_rule: The review rule to search for
            top_k: Number of top results to return
            
        Returns:
            List of relevant policy documents with metadata
        """
        if not self.collection:
            raise RuntimeError("Database not initialized. Call initialize_db() first.")
        
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings.embed_query(review_rule)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for idx in range(len(results['documents'][0])):
                    result = {
                        "document": results['documents'][0][idx],
                        "metadata": results['metadatas'][0][idx],
                        "distance": results['distances'][0][idx],
                        "similarity": 1 - results['distances'][0][idx]  # Convert distance to similarity
                    }
                    formatted_results.append(result)
            
            logger.info(f"Query for '{review_rule}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying policies: {e}")
            raise
    
    def get_policy_by_rule(self, review_rule: str) -> Optional[str]:
        """
        Get the complete policy document for a specific review rule.
        
        Args:
            review_rule: The review rule name
            
        Returns:
            Complete policy document or None if not found
        """
        results = self.query_policy(review_rule, top_k=5)
        
        # Filter results that match the review rule
        matching_results = [
            r for r in results 
            if r['metadata'].get('review_rule', '').upper() == review_rule.upper()
        ]
        
        if matching_results:
            # Combine all chunks from the same policy
            return '\n'.join([r['document'] for r in matching_results])
        
        return None
    
    def list_all_policies(self) -> List[str]:
        """
        List all review rules in the database.
        
        Returns:
            List of unique review rule names
        """
        if not self.collection:
            raise RuntimeError("Database not initialized. Call initialize_db() first.")
        
        try:
            # Get all documents
            all_docs = self.collection.get(include=["metadatas"])
            
            # Extract unique review rules
            review_rules = set()
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    if 'review_rule' in metadata:
                        review_rules.add(metadata['review_rule'])
            
            return sorted(list(review_rules))
            
        except Exception as e:
            logger.error(f"Error listing policies: {e}")
            raise
    
    def reset_collection(self) -> None:
        """
        Reset the collection (delete all documents).
        """
        if self.collection:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Underwriting policy documents"}
            )
            logger.info(f"Collection '{self.collection_name}' reset successfully")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        if not self.collection:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_directory": self.persist_directory,
            "policies": self.list_all_policies()
        }
