import json
import re
import time
from typing import List, Dict, Any
from openai import OpenAI
from app.config import settings
from app.logger import get_logger

logger = get_logger("services.openai_service")

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def parse_prompt_with_openai(prompt: str) -> List[Dict[str, Any]]:
    """Use OpenAI to parse the prompt and extract operations"""
    system_prompt = """You are a prompt parser for a random number calculation engine.
Parse the user's prompt into a JSON array of operations. Each operation should be a JSON object.

Available operations:
1. generate_random - Generate a random number between 0 and 1
   {"type": "generate_random", "variable": "r1"}
   
2. multiply - Multiply two numbers (a and b can be variables or numbers)
   {"type": "multiply", "a": "r1", "b": 0.1234567, "variable": "result1"}
   {"type": "multiply", "a": "sqrt_r2", "b": "prev_result", "variable": "final_result"}
   
3. divide - Divide two numbers (a and b can be variables or numbers)
   {"type": "divide", "a": "r1", "b": 1.1234567, "variable": "result1"}
   
4. square_root - Get square root of a number
   {"type": "square_root", "num": "r2", "variable": "sqrt_r2"}
   
5. conditional - If-then-else (condition compares left and right with operator: <, >, <=, >=, ==, !=)
   {"type": "conditional", "condition": {"left": "r1", "operator": "<", "right": 0.5}, 
    "if_true": [{"type": "multiply", "a": "r1", "b": 0.1234567, "variable": "prev_result"}],
    "if_false": [{"type": "divide", "a": "r1", "b": 1.1234567, "variable": "prev_result"}],
    "variable": "prev_result"}
   
6. assign - Assign a value to a variable (rarely needed, operations auto-assign to variables)
   {"type": "assign", "variable": "prev_result", "value": "result"}

IMPORTANT RULES:
- Always assign results to variables with descriptive names (e.g., "r1", "r2", "prev_result", "final_result")
- When the prompt says "previous result" or "the previous result", reference the variable that stored it
- Operations execute sequentially - use variable names to reference earlier results
- For "multiply it by the previous result", use the variable name that stored the previous result
- Return ONLY a valid JSON array of operations (starting with [ and ending with ]), no other text, no markdown code blocks, no wrapping objects
- The response must be a JSON array, not a JSON object containing an array

Example for: "Generate a random number. If the number is less than 0.5, multiply it by 0.1234567, otherwise divide it by 1.1234567. Generate another random number, get the square root of it, and then multiply it by the previous result."

[
  {"type": "generate_random", "variable": "r1"},
  {"type": "conditional", 
   "condition": {"left": "r1", "operator": "<", "right": 0.5},
   "if_true": [{"type": "multiply", "a": "r1", "b": 0.1234567, "variable": "prev_result"}],
   "if_false": [{"type": "divide", "a": "r1", "b": 1.1234567, "variable": "prev_result"}],
   "variable": "prev_result"},
  {"type": "generate_random", "variable": "r2"},
  {"type": "square_root", "num": "r2", "variable": "sqrt_r2"},
  {"type": "multiply", "a": "sqrt_r2", "b": "prev_result", "variable": "final_result"}
]"""

    try:
        logger.debug(f"Calling OpenAI API with prompt length: {len(prompt)} characters")
        api_start = time.time()
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        api_duration = time.time() - api_start
        logger.info(f"OpenAI API call completed in {api_duration:.3f}s")
        
        content = response.choices[0].message.content.strip()
        logger.debug(f"Raw OpenAI response length: {len(content)} characters")
        logger.debug(f"Raw OpenAI response (first 200 chars): {content[:200]}...")
        
        # Remove markdown code blocks if present (in case model still adds them)
        content = re.sub(r'```json\n?', '', content)
        content = re.sub(r'```\n?', '', content)
        content = content.strip()
        
        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            logger.debug(f"Successfully parsed JSON response")
            
            # If it's a JSON object, try to get the operations array
            if isinstance(parsed, dict):
                logger.debug(f"Parsed response is a dict, extracting operations array")
                # Check if operations are in a key
                if 'operations' in parsed:
                    operations = parsed['operations']
                elif 'result' in parsed:
                    operations = parsed['result']
                else:
                    # Try to find any array value
                    array_values = [v for v in parsed.values() if isinstance(v, list)]
                    if array_values:
                        operations = array_values[0]
                    else:
                        raise ValueError("Could not find operations array in JSON object")
            elif isinstance(parsed, list):
                operations = parsed
            else:
                raise ValueError(f"Expected a list or dict, got: {type(parsed)}")
            
            # Ensure it's a list
            if not isinstance(operations, list):
                raise ValueError(f"Expected a list of operations, got: {type(operations)}")
            
            logger.info(f"Successfully parsed {len(operations)} operations from OpenAI response")
            logger.debug(f"Operations: {json.dumps(operations, indent=2)}")
            
            return operations
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Failed to parse content (first 500 chars): {content[:500]}")
            raise ValueError(f"Failed to parse JSON from OpenAI response: {str(e)}\nResponse: {content[:200]}")
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to parse prompt with OpenAI: {str(e)}")

