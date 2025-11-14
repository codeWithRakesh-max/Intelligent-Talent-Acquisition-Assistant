from typing import List, Dict, Any
import json
import os

class VectorDatabase:
    def __init__(self):
        self.data_dir = "data/simple_db"
        os.makedirs(self.data_dir, exist_ok=True)
        self.candidates_file = os.path.join(self.data_dir, "candidates.json")
        self.jobs_file = os.path.join(self.data_dir, "jobs.json")
        
        # Initialize empty collections
        if not os.path.exists(self.candidates_file):
            with open(self.candidates_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'w') as f:
                json.dump({}, f)

    def add_candidate(self, candidate_id: str, resume_text: str, metadata: Dict[str, Any]):
        """Add a candidate's resume to the database"""
        with open(self.candidates_file, 'r') as f:
            candidates = json.load(f)
        
        candidates[candidate_id] = {
            "document": resume_text,
            "metadata": metadata
        }
        
        with open(self.candidates_file, 'w') as f:
            json.dump(candidates, f)

    def add_job(self, job_id: str, job_description: str, metadata: Dict[str, Any]):
        """Add a job description to the database"""
        with open(self.jobs_file, 'r') as f:
            jobs = json.load(f)
        
        jobs[job_id] = {
            "document": job_description,
            "metadata": metadata
        }
        
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f)

    def search_candidates(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for candidates matching a query (simple implementation)"""
        try:
            with open(self.candidates_file, 'r') as f:
                candidates = json.load(f)
            
            # Simple search implementation
            results = []
            for id, data in candidates.items():
                if query.lower() in data["document"].lower():
                    results.append({
                        "id": id,
                        "document": data["document"],
                        "metadata": data["metadata"]
                    })
            
            results = results[:n_results]
            return {
                "ids": [r["id"] for r in results],
                "documents": [r["document"] for r in results],
                "metadatas": [r["metadata"] for r in results],
                "distances": [1.0] * len(results)  # Placeholder distances
            }
        except Exception as e:
            print(f"Error searching candidates: {e}")
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "distances": []
            }

    def search_jobs(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for jobs matching a query (simple implementation)"""
        try:
            with open(self.jobs_file, 'r') as f:
                jobs = json.load(f)
            
            # Simple search implementation
            results = []
            for id, data in jobs.items():
                if query.lower() in data["document"].lower():
                    results.append({
                        "id": id,
                        "document": data["document"],
                        "metadata": data["metadata"]
                    })
            
            results = results[:n_results]
            return {
                "ids": [r["id"] for r in results],
                "documents": [r["document"] for r in results],
                "metadatas": [r["metadata"] for r in results],
                "distances": [1.0] * len(results)  # Placeholder distances
            }
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "distances": []
            }

    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Get a specific candidate's information"""
        try:
            with open(self.candidates_file, 'r') as f:
                candidates = json.load(f)
            
            if candidate_id in candidates:
                return {
                    "ids": [candidate_id],
                    "documents": [candidates[candidate_id]["document"]],
                    "metadatas": [candidates[candidate_id]["metadata"]]
                }
            return {
                "ids": [],
                "documents": [],
                "metadatas": []
            }
        except Exception as e:
            print(f"Error getting candidate: {e}")
            return {
                "ids": [],
                "documents": [],
                "metadatas": []
            }

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get a specific job's information"""
        try:
            with open(self.jobs_file, 'r') as f:
                jobs = json.load(f)
            
            if job_id in jobs:
                return {
                    "ids": [job_id],
                    "documents": [jobs[job_id]["document"]],
                    "metadatas": [jobs[job_id]["metadata"]]
                }
            return {
                "ids": [],
                "documents": [],
                "metadatas": []
            }
        except Exception as e:
            print(f"Error getting job: {e}")
            return {
                "ids": [],
                "documents": [],
                "metadatas": []
            }