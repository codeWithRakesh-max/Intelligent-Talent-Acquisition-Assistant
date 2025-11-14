from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from utils.prompts import SOURCING_PROMPT
from utils.database import VectorDatabase
from utils.external_sourcing import ExternalSourcer
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
load_dotenv()

class SourcingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0.7,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        self.chain = SOURCING_PROMPT | self.llm
        self.db = VectorDatabase()
        self.external_sourcer = ExternalSourcer()

    def source_candidates(self, job_description: str, requirements: str) -> Dict[str, Any]:
        """Generate search queries and find potential candidates"""
        # For direct search queries, skip LLM
        if job_description == requirements:
            search_queries = [job_description]
        else:
            # Get search queries from LLM
            response = self.chain.invoke({
                "job_description": job_description,
                "requirements": requirements
            })
            search_queries = response.content.split('\n') if hasattr(response, 'content') else str(response).split('\n')
        
        candidates = []
        # Search external sources first
        for query in search_queries:
            if query.strip():
                # Search GitHub
                github_results = self.external_sourcer.search_github(query.strip())
                if github_results:
                    candidates.extend(github_results)
                
                # Search internal database
                db_results = self.db.search_candidates(query)
                if db_results and 'ids' in db_results:
                    for i in range(len(db_results['ids'])):
                        candidate = {
                            'id': str(db_results['ids'][i]),
                            'metadata': db_results['metadatas'][i],
                            'source': 'Internal Database'
                        }
                        candidates.append(candidate)

        # Remove duplicates
        unique_candidates = {}
        for candidate in candidates:
            candidate_id = str(candidate.get('id', ''))
            if candidate_id and candidate_id not in unique_candidates:
                # Normalize the data structure
                if 'metadata' not in candidate:
                    candidate = self.external_sourcer.normalize_candidate_data(candidate)
                unique_candidates[candidate_id] = candidate

        # Add any new external candidates to the database
        for candidate in candidates:
            if candidate.get('source') != 'Internal Database':
                candidate_id = str(candidate.get('id', ''))
                if candidate_id and not self.db.get_candidate(candidate_id).get('ids'):
                    normalized = self.external_sourcer.normalize_candidate_data(candidate)
                    self.add_candidate_to_database(
                        candidate_id,
                        normalized.get('document', ''),
                        normalized.get('metadata', {})
                    )

        return {
            "search_queries": search_queries,
            "candidates": list(unique_candidates.values())
        }

    def add_candidate_to_database(self, candidate_id: str, resume_text: str, metadata: Dict[str, Any]):
        """Add a new candidate to the database"""
        self.db.add_candidate(candidate_id, resume_text, metadata)