"""
RAG Policy Engine
Retrieval-Augmented Generation for POJK policy compliance
Uses Weaviate vector database for semantic search
"""
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth

load_dotenv()


class RAGPolicyEngine:
    """
    RAG engine for policy compliance checking
    
    Stores and retrieves:
    - POJK regulations (33/2018, 1/2024, 29/2024)
    - Internal lending policies
    - Risk management guidelines
    """
    
    def __init__(self):
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")
        
        # Connect to Weaviate
        try:
            if weaviate_api_key:
                self.client = weaviate.connect_to_custom(
                    http_host=weaviate_url.replace("http://", "").replace("https://", ""),
                    http_port=80,
                    http_secure=False,
                    auth_credentials=Auth.api_key(weaviate_api_key)
                )
            else:
                self.client = weaviate.connect_to_local(
                    host=weaviate_url.replace("http://", "").split(":")[0],
                    port=int(weaviate_url.split(":")[-1]) if ":" in weaviate_url else 8080
                )
            
            # Create schema if not exists
            self._ensure_schema()
        
        except Exception as e:
            print(f"Warning: Weaviate connection failed: {e}")
            self.client = None
    
    def _ensure_schema(self):
        """Create Weaviate schema for policy documents"""
        if not self.client:
            return
        
        try:
            # Check if collection exists
            collections = self.client.collections.list_all()
            
            if "PolicyDocument" not in [c.name for c in collections]:
                # Create collection
                self.client.collections.create(
                    name="PolicyDocument",
                    description="POJK regulations and lending policies",
                    properties=[
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Document title"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content"
                        },
                        {
                            "name": "policy_type",
                            "dataType": ["text"],
                            "description": "Type: POJK, INTERNAL, RISK_MANAGEMENT"
                        },
                        {
                            "name": "regulation_number",
                            "dataType": ["text"],
                            "description": "E.g., POJK 33/2018"
                        },
                        {
                            "name": "effective_date",
                            "dataType": ["date"],
                            "description": "When policy became effective"
                        }
                    ],
                    vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_transformers()
                )
                
                print("✓ PolicyDocument collection created")
        
        except Exception as e:
            print(f"Schema creation error: {e}")
    
    async def index_policy(
        self,
        title: str,
        content: str,
        policy_type: str,
        regulation_number: Optional[str] = None,
        effective_date: Optional[str] = None
    ) -> bool:
        """
        Index a policy document into Weaviate
        
        Args:
            title: Policy title
            content: Full policy content
            policy_type: POJK, INTERNAL, RISK_MANAGEMENT
            regulation_number: E.g., "POJK 33/2018"
            effective_date: ISO date string
        
        Returns:
            Success boolean
        """
        if not self.client:
            print("Weaviate client not initialized")
            return False
        
        try:
            collection = self.client.collections.get("PolicyDocument")
            
            collection.data.insert(
                properties={
                    "title": title,
                    "content": content,
                    "policy_type": policy_type,
                    "regulation_number": regulation_number or "",
                    "effective_date": effective_date or "2024-01-01T00:00:00Z"
                }
            )
            
            return True
        
        except Exception as e:
            print(f"Indexing error: {e}")
            return False
    
    async def query_policies(
        self,
        query: str,
        limit: int = 5,
        policy_type: Optional[str] = None
    ) -> Dict:
        """
        Semantic search for relevant policies
        
        Args:
            query: Natural language query
            limit: Maximum results to return
            policy_type: Filter by policy type (optional)
        
        Returns:
            Dict with matched documents and relevance scores
        """
        if not self.client:
            return {
                "query": query,
                "documents": [],
                "message": "RAG engine not available"
            }
        
        try:
            collection = self.client.collections.get("PolicyDocument")
            
            # Build query
            search_query = collection.query.near_text(
                query=query,
                limit=limit
            )
            
            # Execute
            response = search_query
            
            # Format results
            documents = []
            for obj in response.objects:
                documents.append({
                    "title": obj.properties.get("title", ""),
                    "content": obj.properties.get("content", "")[:500],  # First 500 chars
                    "policy_type": obj.properties.get("policy_type", ""),
                    "regulation_number": obj.properties.get("regulation_number", ""),
                    "relevance_score": obj.metadata.score if hasattr(obj.metadata, 'score') else 0.0
                })
            
            return {
                "query": query,
                "documents": documents,
                "count": len(documents)
            }
        
        except Exception as e:
            print(f"Query error: {e}")
            return {
                "query": query,
                "documents": [],
                "error": str(e)
            }
    
    async def check_compliance(
        self,
        application_data: Dict
    ) -> Dict:
        """
        Check if application complies with POJK regulations
        
        Args:
            application_data: Application details
        
        Returns:
            Compliance check result
        """
        # Build compliance query
        query = f"""
        Check POJK compliance for:
        Loan amount: Rp {application_data.get('loan_amount', 0):,.0f}
        Borrower age: {application_data.get('age', 'N/A')}
        Loan term: {application_data.get('loan_term_months', 'N/A')} months
        DTI ratio: {application_data.get('dti_ratio', 'N/A')}
        """
        
        # Query relevant policies
        results = await self.query_policies(query, policy_type="POJK")
        
        # Analyze for violations (simplified)
        violations = []
        
        # Age check
        age = application_data.get('age')
        if age and (age < 21 or age > 65):
            violations.append({
                "rule": "Age Limit",
                "violation": f"Borrower age {age} outside range 21-65",
                "severity": "HIGH"
            })
        
        # DTI check
        dti = application_data.get('dti_ratio')
        if dti and dti > 0.4:
            violations.append({
                "rule": "Debt-to-Income Ratio",
                "violation": f"DTI {dti:.1%} exceeds 40% maximum",
                "severity": "HIGH"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "policy_references": results.get("documents", [])
        }
    
    def close(self):
        """Close Weaviate connection"""
        if self.client:
            self.client.close()
