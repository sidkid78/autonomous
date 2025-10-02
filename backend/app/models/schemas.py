
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union 

class QueryRequest(BaseModel):
    query: str 
    user_id: Optional[str] = None
    session_id: Optional[str] = None 

class WorkflowSelection(BaseModel):
    selected_workflow: str 
    reasoning: str 
    required_agents: List[str]
    personas: Dict[str, Dict[str, Any]]

class AgentResponse(BaseModel):
    agent_role: str
    content: str 
    metadata: Optional[Dict[str, Any]] = None 

class WorkflowResponse(BaseModel):
    final_response: str 
    workflow_info: WorkflowSelection 
    intermediate_steps: List[AgentResponse]
    processing_time: float 
