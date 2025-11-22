"""
Tool Calling Framework for Gemini
Enables Gemini to call external tools/functions for agentic reasoning
"""
from typing import Dict, List, Any, Callable, Optional
import json
import google.generativeai as genai


class Tool:
    """Represents a callable tool/function"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict,
        function: Callable
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function
    
    def to_gemini_function_declaration(self) -> Dict:
        """Convert to Gemini function declaration format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool function"""
        return self.function(**kwargs)


class ToolCallingFramework:
    """
    Framework for Gemini tool calling (function calling)
    
    Allows Gemini to:
    - Query credit bureau data
    - Calculate financial ratios
    - Check policy compliance
    - Retrieve similar cases
    """
    
    def __init__(self, gemini_api_key: str):
        self.tools: Dict[str, Tool] = {}
        genai.configure(api_key=gemini_api_key)
        
        # Initialize default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools for credit underwriting"""
        
        # Tool 1: Calculate DTI
        self.register_tool(Tool(
            name="calculate_dti",
            description="Calculate Debt-to-Income ratio for a borrower",
            parameters={
                "type": "object",
                "properties": {
                    "monthly_income": {
                        "type": "number",
                        "description": "Borrower's monthly income in IDR"
                    },
                    "monthly_payment": {
                        "type": "number",
                        "description": "Proposed monthly loan payment in IDR"
                    },
                    "existing_debt_payment": {
                        "type": "number",
                        "description": "Existing monthly debt payments in IDR"
                    }
                },
                "required": ["monthly_income", "monthly_payment"]
            },
            function=self._calculate_dti
        ))
        
        # Tool 2: Calculate DSCR
        self.register_tool(Tool(
            name="calculate_dscr",
            description="Calculate Debt Service Coverage Ratio",
            parameters={
                "type": "object",
                "properties": {
                    "net_income": {
                        "type": "number",
                        "description": "Monthly net income in IDR"
                    },
                    "total_debt_service": {
                        "type": "number",
                        "description": "Total monthly debt service in IDR"
                    }
                },
                "required": ["net_income", "total_debt_service"]
            },
            function=self._calculate_dscr
        ))
        
        # Tool 3: Query similar cases
        self.register_tool(Tool(
            name="query_similar_cases",
            description="Find similar loan applications and their outcomes",
            parameters={
                "type": "object",
                "properties": {
                    "loan_amount": {
                        "type": "number",
                        "description": "Loan amount to search for"
                    },
                    "credit_score": {
                        "type": "number",
                        "description": "Credit score to match"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of cases to return"
                    }
                },
                "required": ["loan_amount", "credit_score"]
            },
            function=self._query_similar_cases
        ))
        
        # Tool 4: Check POJK compliance
        self.register_tool(Tool(
            name="check_pojk_compliance",
            description="Check if application complies with POJK regulations",
            parameters={
                "type": "object",
                "properties": {
                    "age": {
                        "type": "integer",
                        "description": "Borrower's age"
                    },
                    "dti_ratio": {
                        "type": "number",
                        "description": "Debt-to-Income ratio"
                    },
                    "delinquent_accounts": {
                        "type": "integer",
                        "description": "Number of delinquent accounts"
                    }
                },
                "required": ["age", "dti_ratio"]
            },
            function=self._check_pojk_compliance
        ))
        
        # Tool 5: Calculate amortization
        self.register_tool(Tool(
            name="calculate_amortization",
            description="Calculate loan amortization schedule",
            parameters={
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "number",
                        "description": "Loan principal amount in IDR"
                    },
                    "annual_rate": {
                        "type": "number",
                        "description": "Annual interest rate (e.g., 0.12 for 12%)"
                    },
                    "term_months": {
                        "type": "integer",
                        "description": "Loan term in months"
                    }
                },
                "required": ["principal", "annual_rate", "term_months"]
            },
            function=self._calculate_amortization
        ))
    
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get_function_declarations(self) -> List[Dict]:
        """Get all tool declarations for Gemini"""
        return [tool.to_gemini_function_declaration() for tool in self.tools.values()]
    
    def create_model_with_tools(
        self,
        model_name: str = "gemini-2.0-flash-exp"
    ) -> genai.GenerativeModel:
        """Create Gemini model with tool calling enabled"""
        
        function_declarations = self.get_function_declarations()
        
        model = genai.GenerativeModel(
            model_name=model_name,
            tools=[{
                "function_declarations": function_declarations
            }]
        )
        
        return model
    
    def execute_tool_call(
        self,
        function_name: str,
        function_args: Dict
    ) -> Any:
        """Execute a tool based on Gemini's function call"""
        if function_name not in self.tools:
            raise ValueError(f"Unknown tool: {function_name}")
        
        tool = self.tools[function_name]
        return tool.execute(**function_args)
    
    def run_agentic_loop(
        self,
        prompt: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Run agentic loop with tool calling
        
        Gemini can call tools multiple times to gather information
        before providing final answer
        """
        model = self.create_model_with_tools()
        chat = model.start_chat()
        
        iterations = 0
        tool_calls_history = []
        
        response = chat.send_message(prompt)
        
        while iterations < max_iterations:
            # Check if Gemini wants to call a function
            if not response.candidates[0].content.parts:
                break
            
            part = response.candidates[0].content.parts[0]
            
            # If Gemini returns text (final answer)
            if hasattr(part, 'text'):
                return {
                    'final_answer': part.text,
                    'tool_calls': tool_calls_history,
                    'iterations': iterations
                }
            
            # If Gemini wants to call a function
            elif hasattr(part, 'function_call'):
                function_call = part.function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                # Execute the tool
                try:
                    result = self.execute_tool_call(function_name, function_args)
                    
                    # Record this call
                    tool_calls_history.append({
                        'tool': function_name,
                        'args': function_args,
                        'result': result
                    })
                    
                    # Send result back to Gemini
                    response = chat.send_message({
                        "function_response": {
                            "name": function_name,
                            "response": {"result": result}
                        }
                    })
                    
                except Exception as e:
                    # Send error back to Gemini
                    response = chat.send_message({
                        "function_response": {
                            "name": function_name,
                            "response": {"error": str(e)}
                        }
                    })
            
            else:
                break
            
            iterations += 1
        
        # If we hit max iterations, return what we have
        return {
            'final_answer': "Max iterations reached",
            'tool_calls': tool_calls_history,
            'iterations': iterations
        }
    
    # Tool implementation methods
    
    def _calculate_dti(
        self,
        monthly_income: float,
        monthly_payment: float,
        existing_debt_payment: float = 0
    ) -> Dict:
        """Calculate DTI ratio"""
        total_debt = monthly_payment + existing_debt_payment
        dti = total_debt / monthly_income if monthly_income > 0 else 1.0
        
        return {
            "dti_ratio": round(dti, 4),
            "dti_percentage": f"{dti * 100:.2f}%",
            "compliant": dti <= 0.40,
            "recommendation": "APPROVE" if dti <= 0.30 else "REVIEW" if dti <= 0.40 else "REJECT"
        }
    
    def _calculate_dscr(
        self,
        net_income: float,
        total_debt_service: float
    ) -> Dict:
        """Calculate DSCR"""
        dscr = net_income / total_debt_service if total_debt_service > 0 else 999
        
        return {
            "dscr": round(dscr, 2),
            "compliant": dscr >= 1.25,
            "interpretation": "Strong" if dscr >= 1.5 else "Adequate" if dscr >= 1.25 else "Weak"
        }
    
    def _query_similar_cases(
        self,
        loan_amount: float,
        credit_score: float,
        limit: int = 5
    ) -> List[Dict]:
        """Query similar cases (mock implementation)"""
        # In production, query actual database
        # For now, return mock data
        return [
            {
                "case_id": "CASE001",
                "loan_amount": loan_amount * 0.95,
                "credit_score": credit_score + 10,
                "outcome": "APPROVED",
                "default_status": False
            },
            {
                "case_id": "CASE002",
                "loan_amount": loan_amount * 1.1,
                "credit_score": credit_score - 20,
                "outcome": "REJECTED",
                "default_status": None
            }
        ]
    
    def _check_pojk_compliance(
        self,
        age: int,
        dti_ratio: float,
        delinquent_accounts: int = 0
    ) -> Dict:
        """Check POJK compliance"""
        violations = []
        
        if age < 21 or age > 65:
            violations.append("Age outside acceptable range (21-65)")
        
        if dti_ratio > 0.40:
            violations.append(f"DTI ratio {dti_ratio:.1%} exceeds 40% limit")
        
        if delinquent_accounts > 0:
            violations.append(f"Has {delinquent_accounts} delinquent account(s)")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendation": "PROCEED" if len(violations) == 0 else "REJECT"
        }
    
    def _calculate_amortization(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> Dict:
        """Calculate loan amortization"""
        monthly_rate = annual_rate / 12
        
        # Calculate monthly payment using amortization formula
        if monthly_rate == 0:
            monthly_payment = principal / term_months
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
        
        total_payment = monthly_payment * term_months
        total_interest = total_payment - principal
        
        return {
            "monthly_payment": round(monthly_payment, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "interest_percentage": f"{(total_interest / principal * 100):.2f}%"
        }
