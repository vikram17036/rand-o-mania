import time
import uuid
from fastapi import APIRouter, HTTPException
from app.models import PromptRequest, PromptResponse
from app.services.execution_engine import ExecutionEngine
from app.services.openai_service import parse_prompt_with_openai
from app.logger import get_logger

logger = get_logger("routes.api")
router = APIRouter()

@router.post("/", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    """
    Process a prompt containing random number operations.
    Returns the result and all random numbers generated.
    """
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"[Request {request_id}] Request received - prompt: {request.prompt[:100]}...")
    
    try:
        # Parse the prompt using OpenAI
        logger.info(f"[Request {request_id}] Starting OpenAI parsing...")
        parse_start = time.time()
        operations = parse_prompt_with_openai(request.prompt)
        parse_duration = time.time() - parse_start
        logger.info(f"[Request {request_id}] OpenAI parsing completed in {parse_duration:.3f}s - operations count: {len(operations)}")
        logger.debug(f"[Request {request_id}] Parsed operations: {operations}")
        
        # Execute operations
        logger.info(f"[Request {request_id}] Starting execution engine with {len(operations)} operations")
        exec_start = time.time()
        engine = ExecutionEngine()
        result = engine.execute_operations(operations)
        exec_duration = time.time() - exec_start
        logger.info(f"[Request {request_id}] Execution completed in {exec_duration:.3f}s - final result: {result}")
        
        # Round result to 10 decimal places
        result = round(result, 10)
        
        total_duration = time.time() - start_time
        logger.info(f"[Request {request_id}] Response sent - result: {result}, random_numbers: {engine.random_numbers}, total_duration: {total_duration:.3f}s")
        
        return PromptResponse(
            result=result,
            random_integers=engine.random_numbers
        )
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[Request {request_id}] Error occurred after {error_duration:.3f}s: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy"}

