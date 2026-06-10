import os
from dotenv import load_dotenv
load_dotenv()
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from app.data_loader import DataLoader   # FIX: was "data_loder" (typo)
from app.rbac import RBACHandler

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.rbac = RBACHandler()
        self.data_loader = DataLoader("data")
    
    async def initialize_vector_stores(self):
        """Initialize vector store with all documents"""
        logger.info("📚 Loading documents...")
        documents = self.data_loader.load_all_documents()
        
        if documents:
            logger.info(f"🔧 Creating vector store with {len(documents)} chunks...")
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            logger.info("✅ Vector store initialized successfully!")
        else:
            logger.warning("⚠️ No documents loaded!")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def retrieve(self, query: str, user_role: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant documents based on role"""
        if not self.vector_store:
            return []
        
        # Search for relevant documents
        all_docs = self.vector_store.similarity_search(query, k=top_k * 2)
        
        # Convert to dict format
        documents = []
        for doc in all_docs:
            documents.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "source_category": doc.metadata.get("source_category", "general"),
            })
        
        # Apply RBAC filtering
        from app.models import UserRole
        role_enum = UserRole(user_role) if isinstance(user_role, str) else user_role
        filtered_docs = self.rbac.filter_documents_by_role(role_enum, documents)
        
        return filtered_docs[:top_k]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self, 
        query: str, 
        documents: List[Dict], 
        user_role: str
    ) -> Dict:
        """Generate response using OpenAI"""
        
        if not documents:
            return {
                "answer": "I don't have access to information that can answer this question. This might be because:\n1. No relevant documents exist\n2. Your role doesn't have permission to access this data",
                "sources": [],
                "token_usage": {"total_tokens": 0}
            }
        
        # Prepare context from retrieved documents
        context_parts = []
        for doc in documents:
            context_parts.append(f"[Document: {doc['source']}]\n{doc['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        system_prompt = f"""You are FinSolve AI Assistant, a helpful chatbot for FinSolve Technologies.

USER ROLE: {user_role.upper()}

CRITICAL RULES:
1. ONLY answer using the provided context below
2. If answer isn't in context, say "Based on available documents, I cannot find this information"
3. ALWAYS cite the source document name
4. Be concise and professional
5. Never invent or assume information

CONTEXT:
{context}

Remember to cite your sources! Example: "According to the quarterly report..."""

        try:
            # Call OpenAI API
            completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = completion.choices[0].message.content
            
            # Extract unique sources
            sources = []
            seen = set()
            for doc in documents:
                src = doc['source']
                if src not in seen:
                    seen.add(src)
                    sources.append({
                        "name": src,
                        "category": doc['source_category']
                    })
            
            return {
                "answer": answer,
                "sources": sources,
                "token_usage": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I encountered an error processing your request. Please try again.",
                "sources": [],
                "token_usage": {"total_tokens": 0}
            }