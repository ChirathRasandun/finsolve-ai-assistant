from typing import List, Set, Dict   # FIX: Dict was missing from import
from app.models import UserRole

class RBACHandler:
    """Role-Based Access Control Handler"""
    
    # Define which data sources each role can access
    ROLE_ACCESS = {
        UserRole.FINANCE: {
            "finance", "quarterly_finance", "financial", "budget", "expense"
        },
        UserRole.MARKETING: {
            "marketing", "market_reports", "campaign", "customer"
        },
        UserRole.HR: {
            "hr", "employee_data", "payroll", "attendance"
        },
        UserRole.ENGINEERING: {
            "engineering", "technical", "architecture", "development"
        },
        UserRole.EXECUTIVE: {
            "*"  # Full access to everything
        },
        UserRole.EMPLOYEE: {
            "general", "handbook", "policy", "event", "faq"
        }
    }
    
    # File to category mapping
    FILE_CATEGORIES = {
        "financial_summary.md": "finance",
        "quarterly_financial_report.md": "quarterly_finance",
        "market_report_q4_2024.md": "market_reports",
        "marketing_report_2024.md": "marketing",
        "marketing_report_q1_2024.md": "marketing",
        "marketing_report_q2_2024.md": "marketing",
        "marketing_report_q3_2024.md": "marketing",
        "hr_data.csv": "employee_data",
        "engineering_master_doc.md": "engineering",
        "employee_handbook.md": "handbook",
    }
    
    def get_allowed_categories(self, role: UserRole) -> Set[str]:
        """Get allowed categories for a role"""
        access = self.ROLE_ACCESS.get(role, set())
        
        if "*" in access:
            # Executive gets all categories
            all_cats = set()
            for cats in self.ROLE_ACCESS.values():
                all_cats.update(cats)
            all_cats.discard("*")
            return all_cats
        
        return access
    
    def get_file_category(self, filename: str) -> str:
        """Get category for a file"""
        for file_pattern, category in self.FILE_CATEGORIES.items():
            if file_pattern.lower() in filename.lower():
                return category
        return "general"
    
    def can_access_file(self, role: UserRole, filename: str) -> bool:
        """Check if role can access a file"""
        allowed = self.get_allowed_categories(role)
        file_cat = self.get_file_category(filename)
        
        return file_cat in allowed
    
    def filter_documents_by_role(self, role: UserRole, documents: List[Dict]) -> List[Dict]:
        """Filter documents based on role"""
        allowed = self.get_allowed_categories(role)
        
        if "*" in self.ROLE_ACCESS.get(role, set()):
            return documents  # Executive sees everything
        
        filtered = []
        for doc in documents:
            doc_cat = doc.get("source_category", "general")
            doc_name = doc.get("source", "")
            
            if doc_cat in allowed or self.can_access_file(role, doc_name):
                filtered.append(doc)
        
        return filtered
