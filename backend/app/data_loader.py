import os
import pandas as pd
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter   # FIX: deprecated import
from langchain_core.documents import Document                          # FIX: deprecated import
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_all_documents(self) -> List[Document]:
        """Load all documents from data directory"""
        all_documents = []
        
        # Load finance documents
        finance_dir = os.path.join(self.data_dir, "finance")
        if os.path.exists(finance_dir):
            all_documents.extend(self._load_directory(finance_dir, "finance"))
        
        # Load marketing documents
        marketing_dir = os.path.join(self.data_dir, "marketing")
        if os.path.exists(marketing_dir):
            all_documents.extend(self._load_directory(marketing_dir, "marketing"))
        
        # Load HR documents
        hr_dir = os.path.join(self.data_dir, "hr")
        if os.path.exists(hr_dir):
            all_documents.extend(self._load_directory(hr_dir, "employee_data"))
        
        # Load engineering documents
        eng_dir = os.path.join(self.data_dir, "engineering")
        if os.path.exists(eng_dir):
            all_documents.extend(self._load_directory(eng_dir, "engineering"))
        
        # Load general documents
        general_dir = os.path.join(self.data_dir, "general")
        if os.path.exists(general_dir):
            all_documents.extend(self._load_directory(general_dir, "general"))
        
        logger.info(f"✅ Loaded {len(all_documents)} document chunks")
        return all_documents
    
    def _load_directory(self, directory: str, category: str) -> List[Document]:
        """Load all files from a directory"""
        documents = []
        
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if filename.endswith('.csv'):
                docs = self._load_csv(filepath, category)
            elif filename.endswith(('.md', '.txt')):
                docs = self._load_text(filepath, category)
            else:
                continue
            
            documents.extend(docs)
        
        return documents
    
    def _load_text(self, filepath: str, category: str) -> List[Document]:
        """Load text/markdown file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc = Document(
                page_content=content,
                metadata={
                    "source": os.path.basename(filepath),
                    "source_category": category,
                    "file_type": "text"
                }
            )
            
            return self.text_splitter.split_documents([doc])
            
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return []
    
    def _load_csv(self, filepath: str, category: str) -> List[Document]:
        """Load CSV file"""
        try:
            df = pd.read_csv(filepath)
            documents = []
            
            for _, row in df.iterrows():
                # Create readable text from CSV row
                content = f"Employee: {row.get('full_name', 'Unknown')}\n"
                content += f"Role: {row.get('role', 'Unknown')}\n"
                content += f"Department: {row.get('department', 'Unknown')}\n"
                content += f"Location: {row.get('location', 'Unknown')}\n"
                content += f"Salary: ${row.get('salary', 0):,.2f}\n"
                content += f"Performance Rating: {row.get('performance_rating', 'N/A')}/5\n"
                content += f"Leave Balance: {row.get('leave_balance', 0)} days\n"
                content += f"Attendance: {row.get('attendance_pct', 0)}%\n"
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": os.path.basename(filepath),
                        "source_category": category,
                        "employee_name": row.get('full_name', ''),
                        "file_type": "csv"
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading CSV {filepath}: {e}")
            return []