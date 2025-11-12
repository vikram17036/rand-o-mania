from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
import math
import os
from openai import OpenAI
import json
import re

app = FastAPI(title="Rand-o-mania API")

# Add CORS middleware to allow access from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize OpenAI client
# Using the provided API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    result: float
    random_integers: List[float]

class ExecutionEngine:
    def __init__(self):
        self.random_numbers = []
        self.variables = {}
        
    def generate_random(self) -> float:
        """Generate a random number between 0 and 1"""
        num = random.random()
        # Round to 10 decimal places
        num = round(num, 10)
        self.random_numbers.append(num)
        return num
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        result = a * b
        return round(result, 10)
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers"""
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
        return round(result, 10)
    
    def square_root(self, num: float) -> float:
        """Get square root of a number"""
        if num < 0:
            raise ValueError("Square root of negative number")
        result = math.sqrt(num)
        return round(result, 10)
    
    def execute_operations(self, operations: List[dict]) -> float:
        """Execute a list of operations"""
        result = None
        
        for op in operations:
            op_type = op.get('type')
            
            if op_type == 'generate_random':
                result = self.generate_random()
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'multiply':
                a = self._get_value(op.get('a'))
                b = self._get_value(op.get('b'))
                result = self.multiply(a, b)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'divide':
                a = self._get_value(op.get('a'))
                b = self._get_value(op.get('b'))
                result = self.divide(a, b)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'square_root':
                num = self._get_value(op.get('num'))
                result = self.square_root(num)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'conditional':
                condition = op.get('condition')
                if_true = op.get('if_true', [])
                if_false = op.get('if_false', [])
                
                # Evaluate condition
                cond_result = self._evaluate_condition(condition)
                
                if cond_result:
                    result = self.execute_operations(if_true)
                else:
                    result = self.execute_operations(if_false)
                    
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'assign':
                value = self._get_value(op.get('value'))
                self.variables[op['variable']] = value
                result = value
        
        # Return the last result, or 0.0 if no operations executed
        return result if result is not None else 0.0
    
    def _get_value(self, value):
        """Get value from variable name or direct value"""
        if value is None:
            return 0.0
        # If it's a string and exists in variables, return the variable value
        if isinstance(value, str) and value in self.variables:
            return self.variables[value]
        # Try to convert to float if it's a number (string or numeric)
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _evaluate_condition(self, condition: dict) -> bool:
        """Evaluate a condition"""
        left = self._get_value(condition.get('left'))
        operator = condition.get('operator')
        right = self._get_value(condition.get('right'))
        
        if operator == '<':
            return left < right
        elif operator == '>':
            return left > right
        elif operator == '<=':
            return left <= right
        elif operator == '>=':
            return left >= right
        elif operator == '==':
            return abs(left - right) < 0.0000000001  # Float comparison
        elif operator == '!=':
            return abs(left - right) >= 0.0000000001
        return False

def parse_prompt_with_openai(prompt: str) -> List[dict]:
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
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present (in case model still adds them)
        content = re.sub(r'```json\n?', '', content)
        content = re.sub(r'```\n?', '', content)
        content = content.strip()
        
        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            # If it's a JSON object, try to get the operations array
            if isinstance(parsed, dict):
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
            
            return operations
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from OpenAI response: {str(e)}\nResponse: {content[:200]}")
    except Exception as e:
        raise ValueError(f"Failed to parse prompt with OpenAI: {str(e)}")

@app.post("/", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    """
    Process a prompt containing random number operations.
    Returns the result and all random numbers generated.
    """
    try:
        # Parse the prompt using OpenAI
        operations = parse_prompt_with_openai(request.prompt)
        
        # Execute operations
        engine = ExecutionEngine()
        result = engine.execute_operations(operations)
        
        # Round result to 10 decimal places
        result = round(result, 10)
        
        return PromptResponse(
            result=result,
            random_integers=engine.random_numbers
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

