from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import json
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

load_dotenv()

class ExternalSourcer:
    def __init__(self):
        self.linkedin_api_key = os.getenv("LINKEDIN_API_KEY")
        self.linkedin_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.cache_dir = "data/sourcing_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize API sessions
        self.github_session = requests.Session()
        if self.github_token:
            self.github_session.headers.update({
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            })

    def search_linkedin(self, query: str) -> List[Dict[str, Any]]:
        """Search for candidates on LinkedIn using their REST API"""
        cache_file = os.path.join(self.cache_dir, "linkedin_cache.json")
        cache_duration = timedelta(hours=24)  # Cache results for 24 hours
        
        # Check cache first
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if query in cached_data:
                    cache_time = datetime.fromisoformat(cached_data[query]['timestamp'])
                    if datetime.now() - cache_time < cache_duration:
                        return cached_data[query]['results']

        try:
            # LinkedIn API endpoint for Talent Search
            endpoint = "https://api.linkedin.com/v2/talentSearch"
            
            # Build the search criteria
            params = {
                'q': 'people',
                'keywords': query,
                'start': 0,
                'count': 10,  # Number of results per page
                'fields': 'id,firstName,lastName,headline,location,industry,positions,skills'
            }
            
            headers = {
                'Authorization': f'Bearer {self.linkedin_api_key}',
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            candidates = []
            for element in data.get('elements', []):
                candidate = {
                    "id": f"li_{element['id']}",
                    "name": f"{element.get('firstName', '')} {element.get('lastName', '')}",
                    "title": element.get('headline', ''),
                    "company": element.get('positions', {}).get('elements', [{}])[0].get('companyName', ''),
                    "location": element.get('location', {}).get('name', ''),
                    "skills": [skill['name'] for skill in element.get('skills', {}).get('elements', [])],
                    "experience": self._calculate_experience(element.get('positions', {}).get('elements', [])),
                    "education": self._get_education(element.get('education', {}).get('elements', [])),
                    "source": "LinkedIn"
                }
                candidates.append(candidate)

        except requests.exceptions.RequestException as e:
            print(f"LinkedIn API error: {str(e)}")
            return []

        # Cache the results with timestamp
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
        else:
            cached_data = {}
        
        cached_data[query] = {
            'timestamp': datetime.now().isoformat(),
            'results': candidates
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cached_data, f)

        return candidates

    def search_github(self, query: str) -> List[Dict[str, Any]]:
        """Search for candidates on GitHub using their REST API"""
        cache_file = os.path.join(self.cache_dir, "github_cache.json")
        cache_duration = timedelta(hours=24)  # Cache results for 24 hours
        
        # Check cache first
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if query in cached_data:
                    cache_time = datetime.fromisoformat(cached_data[query]['timestamp'])
                    if datetime.now() - cache_time < cache_duration:
                        return cached_data[query]['results']

        try:
            # GitHub Search API endpoint
            endpoint = "https://api.github.com/search/users"
            
            # Build the search query
            params = {
                'q': query,
                'sort': 'repositories',
                'order': 'desc',
                'per_page': 10
            }
            
            response = self.github_session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            candidates = []
            for user in data.get('items', []):
                # Get detailed user information
                user_response = self.github_session.get(user['url'])
                user_response.raise_for_status()
                user_data = user_response.json()
                
                # Get user's repositories
                repos_response = self.github_session.get(user['repos_url'])
                repos_response.raise_for_status()
                repos_data = repos_response.json()
                
                # Extract languages from repositories
                languages = set()
                for repo in repos_data[:5]:  # Look at top 5 repos
                    if repo.get('language'):
                        languages.add(repo['language'])
                    
                    # Get languages breakdown for the repo
                    if repo.get('languages_url'):
                        lang_response = self.github_session.get(repo['languages_url'])
                        if lang_response.status_code == 200:
                            languages.update(lang_response.json().keys())
                
                candidate = {
                    "id": f"gh_{user['id']}",
                    "username": user['login'],
                    "name": user_data.get('name', ''),
                    "location": user_data.get('location', 'Remote'),
                    "repositories": [repo['name'] for repo in repos_data[:5]],
                    "languages": list(languages),
                    "contributions": user_data.get('public_repos', 0),
                    "company": user_data.get('company', ''),
                    "bio": user_data.get('bio', ''),
                    "source": "GitHub",
                    "profile_url": user['html_url']
                }
                candidates.append(candidate)
                
                # Respect GitHub's rate limiting
                time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"GitHub API error: {str(e)}")
            return []

        # Cache the results with timestamp
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
        else:
            cached_data = {}
        
        cached_data[query] = {
            'timestamp': datetime.now().isoformat(),
            'results': candidates
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cached_data, f)

        return candidates

    def _calculate_experience(self, positions: List[Dict]) -> str:
        """Calculate total years of experience from LinkedIn positions"""
        if not positions:
            return "Not specified"
            
        total_months = 0
        for position in positions:
            start_date = position.get('startDate', {})
            end_date = position.get('endDate', {}) or {'month': datetime.now().month, 'year': datetime.now().year}
            
            if start_date and 'year' in start_date:
                months = (end_date['year'] - start_date['year']) * 12
                months += (end_date.get('month', 12) - start_date.get('month', 1))
                total_months += months
        
        years = total_months // 12
        return f"{years}+ years" if years > 0 else "Less than 1 year"

    def _get_education(self, education: List[Dict]) -> str:
        """Extract highest education from LinkedIn education data"""
        if not education:
            return "Not specified"
            
        # Sort by end date to get the most recent education
        education.sort(key=lambda x: x.get('endDate', {}).get('year', 0), reverse=True)
        
        if education:
            degree = education[0].get('degreeName', '')
            school = education[0].get('schoolName', '')
            if degree and school:
                return f"{degree} from {school}"
            elif school:
                return school
        
        return "Not specified"

    def normalize_candidate_data(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize candidate data from different sources into a standard format"""
        normalized = {
            "id": candidate.get("id", ""),
            "source": candidate.get("source", "Unknown"),
            "metadata": {
                "name": candidate.get("name", candidate.get("username", "")),
                "location": candidate.get("location", ""),
                "title": candidate.get("title", ""),
                "company": candidate.get("company", ""),
                "skills": candidate.get("skills", candidate.get("languages", [])),
                "experience": candidate.get("experience", ""),
                "education": candidate.get("education", ""),
                "profile_url": candidate.get("profile_url", ""),
                "bio": candidate.get("bio", "")
            }
        }
        
        # Create a text representation for the vector database
        text_parts = [
            f"Name: {normalized['metadata']['name']}",
            f"Location: {normalized['metadata']['location']}",
            f"Title: {normalized['metadata']['title']}",
            f"Company: {normalized['metadata']['company']}",
            f"Skills: {', '.join(normalized['metadata']['skills'])}",
            f"Experience: {normalized['metadata']['experience']}",
            f"Education: {normalized['metadata']['education']}",
            f"Bio: {normalized['metadata']['bio']}"
        ]
        normalized["document"] = "\n".join(text_parts)
        
        return normalized

    def search_all_sources(self, query: str) -> List[Dict[str, Any]]:
        """Search across all available sources"""
        all_candidates = []
        
        # Search LinkedIn if API key is available
        if self.linkedin_api_key and self.linkedin_secret:
            linkedin_results = self.search_linkedin(query)
            for candidate in linkedin_results:
                candidate["source"] = "LinkedIn"
                all_candidates.append(self.normalize_candidate_data(candidate))
        
        # Search GitHub if token is available
        if self.github_token:
            github_results = self.search_github(query)
            for candidate in github_results:
                candidate["source"] = "GitHub"
                all_candidates.append(self.normalize_candidate_data(candidate))
        
        return all_candidates
