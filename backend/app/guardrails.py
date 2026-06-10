import re
from typing import Dict, Any
from datetime import datetime
from app.models import User

class GuardrailsManager:
    def __init__(self):
        # PII patterns to detect and block
        self.pii_patterns = {
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        }
        
        # Sensitive keywords (non-HR can't ask)
        self.sensitive_keywords = [
            "salary", "compensation", "bonus", "pay", "income",
            "termination", "fire", "layoff"
        ]
        
        # Rate limiting
        self.query_counts = {}
    
    async def check_query(self, query: str, user: User) -> Dict[str, Any]:
        """Check if query passes all guardrails"""
        query_lower = query.lower()
        
        # Check for PII extraction attempts
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return {
                    "is_safe": False,
                    "message": f"Query contains {pii_type} data which is not allowed",
                    "violation_type": "pii_detection"
                }
        
        # Check sensitive info access (non-HR, non-Executive)
        if user.role.value not in ["hr", "executive"]:
            for keyword in self.sensitive_keywords:
                if keyword in query_lower:
                    return {
                        "is_safe": False,
                        "message": f"You don't have permission to ask about {keyword}",
                        "violation_type": "unauthorized_access"
                    }
        
        # Check for role escalation attempts
        escalation_patterns = [
            "change my role", "give me access", "hack", "bypass", "override"
        ]
        for pattern in escalation_patterns:
            if pattern in query_lower:
                return {
                    "is_safe": False,
                    "message": "Access escalation attempts are prohibited and logged",
                    "violation_type": "role_escalation"
                }
        
        # Rate limiting
        if not await self._check_rate_limit(user):
            return {
                "is_safe": False,
                "message": "Rate limit exceeded. Please wait before asking more questions.",
                "violation_type": "rate_limit"
            }
        
        return {"is_safe": True, "message": "Query passed"}
    
    async def sanitize_response(self, response: Dict, user: User) -> Dict:
        """Remove sensitive info from response"""
        answer = response.get("answer", "")
        
        # Mask PII in response
        for pii_type, pattern in self.pii_patterns.items():
            answer = re.sub(pattern, f"[REDACTED_{pii_type}]", answer)
        
        response["answer"] = answer
        return response
    
    async def _check_rate_limit(self, user: User) -> bool:
        """Simple rate limiting"""
        user_key = user.username
        current_hour = datetime.utcnow().hour
        
        if user_key not in self.query_counts:
            self.query_counts[user_key] = {"hour": current_hour, "count": 0}
        
        if self.query_counts[user_key]["hour"] != current_hour:
            self.query_counts[user_key] = {"hour": current_hour, "count": 0}
        
        self.query_counts[user_key]["count"] += 1
        
        # Max 30 queries per hour
        return self.query_counts[user_key]["count"] <= 30