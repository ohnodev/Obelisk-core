"""
API routes for Obelisk Core
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from pathlib import Path
import importlib.util

# Import config from root directory (proper way without sys.path hack)
_config_path = Path(__file__).parent.parent.parent / "config.py"
if not _config_path.exists():
    raise FileNotFoundError(f"config.py not found at {_config_path}")

spec = importlib.util.spec_from_file_location("config", _config_path)
if spec is None:
    raise ImportError(f"Failed to create spec for config.py at {_config_path}")

if spec.loader is None:
    raise ImportError(f"Spec loader is None for config.py at {_config_path}")

config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
Config = config_module.Config

router = APIRouter()


# Request/Response models
class ConversationMessage(BaseModel):
    """A single message in conversation history"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ConversationContext(BaseModel):
    """Conversation context with messages and memories"""
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="List of conversation messages (Qwen3 format)"
    )
    memories: str = Field(
        default="",
        description="Selected memory summaries for system message"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format expected by ObeliskLLM.generate()"""
        return {
            "messages": [{"role": msg.role, "content": msg.content} for msg in self.messages],
            "memories": self.memories
        }


# Global instances (initialized on first request)
_storage = None
_llm = None
_quantum_service = None
_memory_manager = None

def get_storage():
    """Get storage instance"""
    global _storage
    if _storage is None:
        _storage = Config.get_storage()
    return _storage

def get_llm():
    """Get LLM instance"""
    global _llm
    if _llm is None:
        from ..llm.obelisk_llm import ObeliskLLM
        _llm = ObeliskLLM(storage=get_storage())
    return _llm

def get_quantum_service():
    """Get quantum service instance"""
    global _quantum_service
    if _quantum_service is None:
        from ..quantum.ibm_quantum_service import IBMQuantumService
        _quantum_service = IBMQuantumService(
            api_key=Config.IBM_QUANTUM_API_KEY,
            instance=Config.IBM_QUANTUM_INSTANCE
        )
    return _quantum_service

def get_memory_manager():
    """Get memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        from ..memory.memory_manager import ObeliskMemoryManager
        _memory_manager = ObeliskMemoryManager(
            storage=get_storage(),
            llm=get_llm(),
            mistral_api_key=Config.MISTRAL_API_KEY,
            agent_id=Config.MISTRAL_AGENT_ID,
            mode=Config.MODE
        )
    return _memory_manager


class GenerateRequest(BaseModel):
    """Request model for LLM generation"""
    prompt: str = Field(..., description="User's query/prompt")
    quantum_influence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Quantum influence value (0.0-1.0)"
    )
    conversation_context: Optional[ConversationContext] = Field(
        default=None,
        description="Conversation context with messages and memories"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for memory management"
    )

class GenerateResponse(BaseModel):
    response: str
    tokens_used: Optional[int] = None
    source: str

class QuantumInfluenceRequest(BaseModel):
    circuit: Optional[str] = None

class QuantumInfluenceResponse(BaseModel):
    influence: float
    random_value: float

class EvolveRequest(BaseModel):
    cycle_id: str
    fine_tune: bool = True

class EvolveResponse(BaseModel):
    status: str
    lora_weights_id: Optional[str] = None
    top_contributors: List[Dict[str, Any]]


# LLM Endpoints
@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate response from The Obelisk"""
    try:
        llm = get_llm()
        memory_manager = get_memory_manager()
        
        # Get conversation context if user_id provided (always runs memory selection)
        conversation_context = request.conversation_context
        if request.user_id and not conversation_context:
            # Get context from memory manager (returns dict format)
            context_dict = memory_manager.get_conversation_context(request.user_id, user_query=request.prompt)
            # Convert to ConversationContext model for validation
            conversation_context = ConversationContext(**context_dict) if context_dict else None
        
        # Convert ConversationContext to dict format expected by ObeliskLLM.generate()
        context_dict = conversation_context.to_dict() if conversation_context else None
        
        result = llm.generate(
            query=request.prompt,
            quantum_influence=request.quantum_influence,
            conversation_context=context_dict
        )
        
        # Add to memory if user_id provided (handles storage internally - Option C)
        if request.user_id:
            memory_manager.add_interaction(
                user_id=request.user_id,
                query=request.prompt,
                response=result.get('response', ''),
                cycle_id=None,  # Will auto-detect current cycle if available
                energy=0.0,
                quantum_seed=request.quantum_influence,
                reward_score=0.0
            )
        
        return GenerateResponse(
            response=result.get('response', ''),
            tokens_used=None,  # Could be calculated from model
            source=result.get('source', 'obelisk_llm')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """Health check"""
    try:
        llm = get_llm()
        return {
            "status": "healthy",
            "model_loaded": llm.model is not None,
            "mode": Config.MODE
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "mode": Config.MODE
        }


# Quantum Endpoints
@router.post("/quantum/influence", response_model=QuantumInfluenceResponse)
async def get_quantum_influence(request: QuantumInfluenceRequest):
    """Get quantum influence value"""
    try:
        quantum_service = get_quantum_service()
        result = quantum_service.get_quantum_random(num_qubits=2, shots=128)
        return QuantumInfluenceResponse(
            influence=result.get('value', 0.5),
            random_value=result.get('value', 0.5)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Evolution Endpoints
@router.post("/evolve", response_model=EvolveResponse)
async def evolve(request: EvolveRequest):
    """Process evolution cycle"""
    try:
        from ..evolution.processor import process_evolution_cycle
        
        storage = get_storage()
        llm = get_llm()
        
        result = process_evolution_cycle(
            cycle_id=request.cycle_id,
            storage=storage,
            llm=llm,
            fine_tune_model=request.fine_tune
        )
        
        return EvolveResponse(
            status=result.get('status', 'completed'),
            lora_weights_id=result.get('model_training', {}).get('weight_id') if result.get('model_training') else None,
            top_contributors=result.get('top_contributors', [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evolution/cycle/{cycle_id}")
async def get_cycle_status(cycle_id: str):
    """Get evolution cycle status"""
    try:
        storage = get_storage()
        cycle = storage.get_evolution_cycle(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return cycle
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Memory Endpoints
@router.get("/memory/{user_id}")
async def get_memory(user_id: str):
    """Get conversation context for user"""
    try:
        memory_manager = get_memory_manager()
        # Note: This endpoint doesn't have a query, use empty string (will use most recent memories)
        context = memory_manager.get_conversation_context(user_id, user_query="")
        return {
            "user_id": user_id,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/{user_id}")
async def save_interaction(user_id: str, query: str, response: str):
    """Save interaction to memory"""
    try:
        memory_manager = get_memory_manager()
        memory_manager.add_interaction(user_id, query, response)
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
