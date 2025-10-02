from pydantic import BaseModel, Field
from typing import List, Dict, Any

# The ToolDefinition class now lives here, breaking the circular import.
class ToolDefinition:
    """
    Definition of a tool available to the autonomous agent
    """
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None, function=None):
        self.name = name 
        self.description = description 
        self.parameters = parameters or {}
        self.function = function 

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for use in prompts"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class AgentResponse(BaseModel):
    agent_role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowSelection(BaseModel):
    personas: Dict[str, Any]

class WorkflowRequest(BaseModel):
    user_query: str

class WorkflowResponse(BaseModel):
    workflow_type: str
    response: str
    intermediate_steps: List[AgentResponse] = []