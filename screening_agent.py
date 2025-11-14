from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from utils.prompts import SCREENING_PROMPT
import os
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()



class ScreeningAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0.3,  # Lower temperature for more consistent screening
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        self.chain = LLMChain(llm=self.llm, prompt=SCREENING_PROMPT)

    def screen_candidate(self, resume: str, job_description: str) -> Dict[str, Any]:
        """Screen a candidate's resume against a job description"""
        result = self.chain.run(
            resume=resume,
            job_description=job_description
        )

        # Parse the result to extract key information
        analysis = {
            "raw_analysis": result,
            "recommendation": self._extract_recommendation(result),
            "key_points": self._extract_key_points(result)
        }

        return analysis

    def _extract_recommendation(self, result: str) -> str:
        """Extract the recommendation from the analysis"""
        if "Strong Match" in result:
            return "Strong Match"
        elif "Potential Match" in result:
            return "Potential Match"
        else:
            return "Not a Match"

    def _extract_key_points(self, result: str) -> Dict[str, str]:
        """Extract key points from the analysis"""
        key_points = {
            "skills_match": "",
            "experience_match": "",
            "education_match": "",
            "cultural_fit": ""
        }

        # Simple extraction logic - can be enhanced
        for line in result.split('\n'):
            if "Skills" in line:
                key_points["skills_match"] = line
            elif "Experience" in line:
                key_points["experience_match"] = line
            elif "Education" in line:
                key_points["education_match"] = line
            elif "Cultural" in line:
                key_points["cultural_fit"] = line

        return key_points 