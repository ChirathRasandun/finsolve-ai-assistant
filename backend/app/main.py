from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.auth import AuthHandler
from app.rag_engine import RAGEngine
from app.guardrails import GuardrailsManager
from app.monitoring import MonitoringManager
from app.models import QueryRequest, QueryResponse, User
# FIX: removed stale unused import of HuggingFaceEmbeddings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
auth_handler = AuthHandler()
rag_engine = RAGEngine()
guardrails = GuardrailsManager()
monitoring = MonitoringManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting FinSolve AI Assistant...")
    await rag_engine.initialize_vector_stores()
    logger.info("✅ System ready!")
    yield
    logger.info("👋 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="FinSolve AI Assistant",
    description="RAG-based chatbot with RBAC",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "FinSolve AI Assistant API",
        "status": "running",
        "endpoints": ["/login", "/query", "/health"]
    }

@app.post("/login")
async def login(username: str, password: str):
    """Authenticate user"""
    user = auth_handler.authenticate(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = auth_handler.create_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.dict()
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user: User = Depends(auth_handler.get_current_user)
):
    """Process user query with RBAC"""
    
    logger.info(f"📝 Processing query from {user.username} ({user.role.value})")
    
    # 1. Check guardrails
    safety_check = await guardrails.check_query(request.query, user)
    if not safety_check["is_safe"]:
        monitoring.log_violation(user, request.query, safety_check)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=safety_check["message"]
        )
    
    # 2. Retrieve relevant documents (with RBAC)
    documents = await rag_engine.retrieve(
        query=request.query,
        user_role=user.role.value,
        top_k=request.top_k or 5
    )
    
    # 3. Generate response
    response = await rag_engine.generate_response(
        query=request.query,
        documents=documents,
        user_role=user.role.value
    )
    
    # 4. Sanitize response
    response = await guardrails.sanitize_response(response, user)
    
    # 5. Log for monitoring
    await monitoring.log_query(
        user=user,
        query=request.query,
        response=response,
        documents=documents,
        token_usage=response.get("token_usage", {})
    )
    
    return QueryResponse(
        answer=response["answer"],
        sources=response["sources"],
        role=user.role.value,
        token_usage=response.get("token_usage", {})
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "queries_logged": len(monitoring.query_logs),
        "total_cost": monitoring.total_cost
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
