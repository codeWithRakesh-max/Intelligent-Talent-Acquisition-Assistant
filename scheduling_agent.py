from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from utils.prompts import SCHEDULING_PROMPT
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()


class SchedulingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0.2,  # Very low temperature for consistent scheduling
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        self.chain = LLMChain(llm=self.llm, prompt=SCHEDULING_PROMPT)
        self.scheduled_interviews = {}

    def find_available_slots(self, candidate_availability: Dict[str, List[str]], 
                           interviewer_availability: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find available time slots for interviews"""
        result = self.chain.run(
            candidate_availability=str(candidate_availability),
            interviewer_availability=str(interviewer_availability)
        )

        # Parse the result to extract time slots
        slots = self._parse_time_slots(result)
        return slots

    def schedule_interview(self, candidate_id: str, slot: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an interview for a specific time slot"""
        interview_id = f"interview_{len(self.scheduled_interviews) + 1}"
        
        interview_details = {
            "id": interview_id,
            "candidate_id": candidate_id,
            "time": slot["time"],
            "duration": slot.get("duration", "60 minutes"),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        self.scheduled_interviews[interview_id] = interview_details
        return interview_details

    def _parse_time_slots(self, result: str) -> List[Dict[str, Any]]:
        """Parse the LLM output to extract time slots"""
        slots = []
        for line in result.split('\n'):
            if ":" in line and ("AM" in line or "PM" in line):
                try:
                    time_str = line.split(":")[1].strip()
                    slots.append({
                        "time": time_str,
                        "duration": "60 minutes"
                    })
                except:
                    continue
        return slots

    def get_scheduled_interviews(self, candidate_id: str = None) -> List[Dict[str, Any]]:
        """Get all scheduled interviews or filter by candidate"""
        if candidate_id:
            return [
                interview for interview in self.scheduled_interviews.values()
                if interview["candidate_id"] == candidate_id
            ]
        return list(self.scheduled_interviews.values())

    def update_interview_status(self, interview_id: str, status: str):
        """Update the status of a scheduled interview"""
        if interview_id in self.scheduled_interviews:
            self.scheduled_interviews[interview_id]["status"] = status 