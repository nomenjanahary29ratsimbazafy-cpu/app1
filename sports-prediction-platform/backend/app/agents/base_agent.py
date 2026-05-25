"""
Base Agent class for the multi-agent system.
All specialized agents inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
import asyncio
from enum import Enum

from app.core.logging import get_logger
from app.core.config import get_settings

settings = get_settings()
logger = get_logger("agent.base")


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentResult:
    """Standardized result from agent execution."""
    
    def __init__(
        self,
        success: bool,
        data: Dict[str, Any],
        confidence: float,
        processing_time_ms: int,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.data = data
        self.confidence = min(max(confidence, 0.0), 1.0)
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}
        self.error = error
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    Each agent is responsible for a specific aspect of the prediction pipeline.
    Agents should be stateless and thread-safe.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.status = AgentStatus.IDLE
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_processing_time_ms = 0
        self.last_error: Optional[str] = None
        self.last_error_at: Optional[datetime] = None
        self.logger = get_logger(f"agent.{name.lower()}")
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Args:
            input_data: Dictionary containing all necessary input data
            
        Returns:
            AgentResult with analysis output and confidence score
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Wrapper method that handles execution with error handling and metrics.
        """
        start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        self.total_executions += 1
        
        try:
            result = await self.execute(input_data)
            
            if result.success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1
                self.last_error = result.error
            
            self.total_processing_time_ms += result.processing_time_ms
            
            self.status = AgentStatus.IDLE
            
            await self.logger.info(
                "agent_execution",
                agent_name=self.name,
                success=result.success,
                confidence=result.confidence,
                processing_time_ms=result.processing_time_ms,
            )
            
            return result
            
        except Exception as e:
            self.failed_executions += 1
            self.last_error = str(e)
            self.last_error_at = datetime.utcnow()
            self.status = AgentStatus.ERROR
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.logger.error(
                "agent_execution_failed",
                agent_name=self.name,
                error=str(e),
                processing_time_ms=processing_time,
            )
            
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e),
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        avg_processing_time = (
            self.total_processing_time_ms / self.total_executions
            if self.total_executions > 0
            else 0
        )
        
        success_rate = (
            self.successful_executions / self.total_executions
            if self.total_executions > 0
            else 0
        )
        
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": round(success_rate, 4),
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "last_error": self.last_error,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
        }
    
    async def health_check(self) -> bool:
        """Check if agent is healthy and ready to process."""
        return self.status != AgentStatus.ERROR


class AsyncAgent(BaseAgent):
    """
    Base class for agents that require async operations.
    Provides retry logic and timeout handling.
    """
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        timeout_seconds: int = None,
        max_retries: int = None,
    ):
        super().__init__(name, version)
        self.timeout_seconds = timeout_seconds or settings.AGENT_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.AGENT_RETRY_COUNT
    
    async def run_with_retry(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute agent with retry logic."""
        last_result = None
        
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.run(input_data),
                    timeout=self.timeout_seconds,
                )
                
                if result.success:
                    return result
                
                last_result = result
                
            except asyncio.TimeoutError:
                await self.logger.warning(
                    "agent_timeout",
                    agent_name=self.name,
                    attempt=attempt + 1,
                    timeout=self.timeout_seconds,
                )
                last_result = AgentResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    processing_time_ms=self.timeout_seconds * 1000,
                    error=f"Timeout after {self.timeout_seconds}s",
                )
            
            except Exception as e:
                await self.logger.warning(
                    "agent_error_retry",
                    agent_name=self.name,
                    attempt=attempt + 1,
                    error=str(e),
                )
        
        return last_result
