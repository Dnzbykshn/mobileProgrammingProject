from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's input message to the AI therapist", example="Bugün kendimi çok yorgun hissediyorum.")
    conversation_id: Optional[str] = Field(None, description="UUID of existing conversation to continue", example="550e8400-e29b-41d4-a716-446655440000")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Selam, biraz konuşabilir miyiz?",
                "conversation_id": None
            }
        }


class ChatResponse(BaseModel):
    intent: str = Field(..., description="Detected intent: CHAT, GATHERING, PROPOSING, READY, CRISIS, etc.", example="CHAT")
    response_text: Optional[str] = Field(None, description="AI's reply text", example="Aleykümselam, tabii ki. Seni dinliyorum.")
    conversation_id: Optional[str] = Field(None, description="UUID of the conversation")
    phase: Optional[str] = Field(None, description="Current conversation phase (IDLE, GATHERING, ONGOING, etc.)", example="ONGOING")
    gathering_progress: Optional[int] = Field(None, description="0-100 progress towards completing the gathering phase")
    crisis_level: Optional[str] = Field(None, description="Crisis severity if detected (immediate, high, moderate)")
    emergency_contacts: Optional[List[dict]] = Field(None, description="List of emergency contacts if crisis detected")
    pathway_id: Optional[str] = Field(None, description="Pathway ID if a pathway was created or updated")
    pathway_action: Optional[str] = Field(None, description="created, updated, failed or authentication_required")
    proposal_summary: Optional[str] = Field(None, description="Summary of the proposed pathway (PROPOSING phase)")
