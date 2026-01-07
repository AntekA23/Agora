from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Base class for all AI agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name."""
        pass

    @property
    @abstractmethod
    def department(self) -> str:
        """Department this agent belongs to."""
        pass

    @abstractmethod
    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's task."""
        pass
