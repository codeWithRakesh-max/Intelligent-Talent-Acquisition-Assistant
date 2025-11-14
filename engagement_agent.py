from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from utils.prompts import ENGAGEMENT_PROMPT
import os
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

class EngagementAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0.8,  # Higher temperature for more creative engagement
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        self.chain = LLMChain(llm=self.llm, prompt=ENGAGEMENT_PROMPT)
        self.conversation_history = {}

    def generate_outreach(self, candidate_info: Dict[str, Any], job_details: Dict[str, Any]) -> str:
        """Generate an initial outreach message"""
        message = self.chain.run(
            candidate_info=str(candidate_info),
            job_details=str(job_details)
        )
        return message

    def handle_candidate_response(self, candidate_id: str, message: str) -> str:
        """Handle a candidate's response and generate a reply"""
        if candidate_id not in self.conversation_history:
            self.conversation_history[candidate_id] = []

        self.conversation_history[candidate_id].append({
            "role": "candidate",
            "content": message
        })

        # Generate context-aware response
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[candidate_id]
        ])

        response = self.llm.predict(
            f"""Based on the following conversation history, generate a professional and engaging response:
            
            {context}
            
            Assistant: """
        )

        self.conversation_history[candidate_id].append({
            "role": "assistant",
            "content": response
        })

        return response

    def get_conversation_history(self, candidate_id: str) -> list:
        """Get the conversation history for a candidate"""
        return self.conversation_history.get(candidate_id, []) 