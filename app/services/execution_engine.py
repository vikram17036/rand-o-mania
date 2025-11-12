import random
import math
from typing import List, Dict, Any
from app.logger import get_logger

logger = get_logger("services.execution_engine")

class ExecutionEngine:
    """Engine for executing random number operations"""
    
    def __init__(self):
        self.random_numbers = []
        self.variables = {}
        self.operation_count = 0
        
    def generate_random(self) -> float:
        """Generate a random number between 0 and 1"""
        num = random.random()
        # Round to 10 decimal places
        num = round(num, 10)
        self.random_numbers.append(num)
        logger.info(f"Generated random number: {num}")
        return num
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        result = a * b
        result = round(result, 10)
        logger.info(f"Multiply: {a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers"""
        if b == 0:
            logger.error(f"Division by zero attempted: {a} / {b}")
            raise ValueError("Division by zero")
        result = a / b
        result = round(result, 10)
        logger.info(f"Divide: {a} / {b} = {result}")
        return result
    
    def square_root(self, num: float) -> float:
        """Get square root of a number"""
        if num < 0:
            logger.error(f"Square root of negative number attempted: sqrt({num})")
            raise ValueError("Square root of negative number")
        result = math.sqrt(num)
        result = round(result, 10)
        logger.info(f"Square root: sqrt({num}) = {result}")
        return result
    
    def execute_operations(self, operations: List[Dict[str, Any]]) -> float:
        """Execute a list of operations"""
        result = None
        total_ops = len(operations)
        
        for idx, op in enumerate(operations, 1):
            op_type = op.get('type')
            logger.info(f"Operation {op_type}")
            
            if op_type == 'generate_random':
                result = self.generate_random()
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'multiply':
                a = self._get_value(op.get('a'))
                b = self._get_value(op.get('b'))
                logger.info(f"Multiplying {a} by {b}")
                result = self.multiply(a, b)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'divide':
                a = self._get_value(op.get('a'))
                b = self._get_value(op.get('b'))
                logger.info(f"Dividing {a} by {b}")
                result = self.divide(a, b)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'square_root':
                num = self._get_value(op.get('num'))
                logger.info(f"Getting square root of {num}")
                result = self.square_root(num)
                if 'variable' in op:
                    self.variables[op['variable']] = result
                    
            elif op_type == 'conditional':
                condition = op.get('condition')
                if_true = op.get('if_true', [])
                if_false = op.get('if_false', [])
                
                # Evaluate condition and log in natural language
                left = self._get_value(condition.get('left'))
                operator = condition.get('operator')
                right = self._get_value(condition.get('right'))
                cond_result = self._evaluate_condition(condition)
                
                # Create natural language condition description
                operator_text = {
                    '<': 'is less than',
                    '>': 'is greater than',
                    '<=': 'is less than or equal to',
                    '>=': 'is greater than or equal to',
                    '==': 'equals',
                    '!=': 'does not equal'
                }.get(operator, operator)
                
                branch_text = 'if_true' if cond_result else 'if_false'
                logger.info(f"Number {left} {operator_text} {right}, so executing {branch_text} branch")
                
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
                logger.info(f"Assigning value {value} to variable '{op['variable']}'")
            else:
                logger.warning(f"Unknown operation type: {op_type}")
        
        # Log final state
        logger.info(f"Execution completed - result: {result}, variables: {self.variables}, random_numbers: {self.random_numbers}")
        
        # Return the last result, or 0.0 if no operations executed
        return result if result is not None else 0.0
    
    def _get_value(self, value: Any) -> float:
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
    
    def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition"""
        left = self._get_value(condition.get('left'))
        operator = condition.get('operator')
        right = self._get_value(condition.get('right'))
        
        if operator == '<':
            result = left < right
        elif operator == '>':
            result = left > right
        elif operator == '<=':
            result = left <= right
        elif operator == '>=':
            result = left >= right
        elif operator == '==':
            result = abs(left - right) < 0.0000000001  # Float comparison
        elif operator == '!=':
            result = abs(left - right) >= 0.0000000001
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
        
        return result

