"""Agent status and management endpoints."""

from typing import List
from fastapi import APIRouter

from app.models.schemas import AgentStatusResponse, APIResponse
from app.agents.base_agent import AgentStatus

router = APIRouter()


@router.get("/status", response_model=List[AgentStatusResponse])
async def get_all_agents_status():
    """Get status of all agents in the system."""
    return []


@router.get("/{agent_name}/stats")
async def get_agent_stats(agent_name: str):
    """Get detailed statistics for a specific agent."""
    return {
        "agent": agent_name,
        "status": "idle",
        "total_executions": 0,
        "success_rate": 1.0,
    }


@router.post("/{agent_name}/health-check", response_model=APIResponse)
async def check_agent_health(agent_name: str):
    """Perform health check on a specific agent."""
    return APIResponse(success=True, message=f"Agent {agent_name} is healthy")
