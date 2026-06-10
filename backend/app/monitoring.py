import json
import time
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MonitoringManager:
    def __init__(self):
        self.query_logs = []
        self.total_cost = 0.0
        
    async def log_query(
        self,
        user,
        query: str,
        response: Dict,
        documents: List[Dict],
        token_usage: Dict
    ):
        """Log all queries for monitoring"""
        
        # Calculate cost (GPT-3.5-turbo pricing)
        prompt_cost = token_usage.get("prompt_tokens", 0) * 0.0015 / 1000
        completion_cost = token_usage.get("completion_tokens", 0) * 0.002 / 1000
        cost = prompt_cost + completion_cost
        self.total_cost += cost
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user.username,
            "role": user.role.value,
            "query": query[:200],
            "response_preview": response.get("answer", "")[:200],
            "documents_retrieved": len(documents),
            "token_usage": token_usage,
            "cost": cost,
            "total_cost": self.total_cost,
            "response_time": time.time()
        }
        
        self.query_logs.append(log_entry)
        
        # Print to console
        logger.info(f"📊 Query | User: {user.username} | Role: {user.role.value}")
        logger.info(f"   Question: {query[:100]}...")
        logger.info(f"   Tokens: {token_usage.get('total_tokens', 0)} | Cost: ${cost:.4f}")
        
        # Save to file
        with open("query_logs.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Alert on high cost
        if cost > 0.01:
            logger.warning(f"⚠️ High cost query: ${cost:.4f}")
    
    def log_violation(self, user, query: str, guardrail_check: Dict):
        """Log security violations"""
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user.username,
            "role": user.role.value,
            "query": query,
            "violation": guardrail_check.get("violation_type", "unknown"),
            "message": guardrail_check.get("message", "")
        }
        
        logger.warning(f"🚨 VIOLATION: {violation}")
        
        with open("violations_log.json", "a") as f:
            f.write(json.dumps(violation) + "\n")