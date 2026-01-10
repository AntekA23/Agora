"""Agent State Machine for conversation flow management.

Implements a state machine that tracks the conversation stage and
manages transitions between states for multi-turn agent interactions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConversationStage(str, Enum):
    """Stages of a conversation with an agent."""

    IDLE = "idle"  # No active task
    GATHERING = "gathering"  # Collecting required/recommended params
    CONFIRMING = "confirming"  # Showing params for confirmation
    EXECUTING = "executing"  # Task is being executed
    COMPLETED = "completed"  # Task finished, showing results


# Valid state transitions
STATE_TRANSITIONS: dict[tuple[str, str], str] = {
    # From idle
    ("idle", "new_task"): "gathering",
    ("idle", "quick_execute"): "executing",  # When all params provided upfront

    # From gathering
    ("gathering", "params_complete"): "confirming",
    ("gathering", "use_defaults"): "confirming",  # User chose defaults
    ("gathering", "cancel"): "idle",

    # From confirming
    ("confirming", "confirmed"): "executing",
    ("confirming", "modify"): "gathering",  # User wants to change something
    ("confirming", "cancel"): "idle",

    # From executing
    ("executing", "done"): "completed",
    ("executing", "error"): "idle",

    # From completed
    ("completed", "new_task"): "gathering",
    ("completed", "reset"): "idle",
}


@dataclass
class AgentState:
    """State of an agent within a conversation context.

    Tracks the current task, collected parameters, and conversation stage.
    Persisted to MongoDB as part of the conversation document.
    """

    # Current task being worked on
    current_task: str | None = None  # e.g., "instagram_post", "invoice"

    # The original user request that started this task
    original_request: str | None = None

    # Current stage in the conversation flow
    conversation_stage: str = "idle"

    # Parameters collected so far
    gathered_params: dict[str, Any] = field(default_factory=dict)

    # Parameters still needed (required)
    missing_required: list[str] = field(default_factory=list)

    # Parameters that would improve quality (recommended)
    missing_recommended: list[str] = field(default_factory=list)

    # The last question asked to the user
    last_question: str | None = None

    # Which parameter the last question was about
    last_question_param: str | None = None

    # Task IDs created during execution
    task_ids: list[str] = field(default_factory=list)

    # Error message if any
    error: str | None = None

    # History for undo functionality (Phase 5: UX)
    params_history: list[dict[str, Any]] = field(default_factory=list)

    # Maximum history entries to keep
    MAX_HISTORY: int = 5

    def save_params_snapshot(self) -> None:
        """Save current params to history for undo."""
        if self.gathered_params:
            self.params_history.append(self.gathered_params.copy())
            # Keep only last N entries
            if len(self.params_history) > self.MAX_HISTORY:
                self.params_history = self.params_history[-self.MAX_HISTORY:]

    def undo_last_change(self) -> bool:
        """Undo the last parameter change.

        Returns:
            True if undo was successful, False if no history
        """
        if len(self.params_history) >= 1:
            # Pop the last state and restore it
            self.gathered_params = self.params_history.pop()
            return True
        return False

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.params_history) > 0

    def transition(self, event: str) -> bool:
        """Attempt to transition to a new state based on an event.

        Args:
            event: The event triggering the transition

        Returns:
            True if transition was successful, False if invalid
        """
        key = (self.conversation_stage, event)
        new_stage = STATE_TRANSITIONS.get(key)

        if new_stage:
            self.conversation_stage = new_stage
            return True
        return False

    def can_transition(self, event: str) -> bool:
        """Check if a transition is valid without performing it.

        Args:
            event: The event to check

        Returns:
            True if the transition would be valid
        """
        key = (self.conversation_stage, event)
        return key in STATE_TRANSITIONS

    def reset(self) -> None:
        """Reset the state to idle."""
        self.current_task = None
        self.original_request = None
        self.conversation_stage = "idle"
        self.gathered_params = {}
        self.missing_required = []
        self.missing_recommended = []
        self.last_question = None
        self.last_question_param = None
        self.task_ids = []
        self.error = None

    def start_task(
        self,
        task_type: str,
        original_request: str,
        initial_params: dict[str, Any],
        missing_required: list[str],
        missing_recommended: list[str],
    ) -> None:
        """Initialize state for a new task.

        Args:
            task_type: Type of task (e.g., "instagram_post")
            original_request: The user's original message
            initial_params: Parameters extracted from the request
            missing_required: Required params still needed
            missing_recommended: Recommended params to ask about
        """
        self.current_task = task_type
        self.original_request = original_request
        self.gathered_params = initial_params.copy()
        self.missing_required = missing_required.copy()
        self.missing_recommended = missing_recommended.copy()
        self.task_ids = []
        self.error = None

        # Determine initial stage
        if missing_required:
            self.conversation_stage = "gathering"
        elif missing_recommended:
            self.conversation_stage = "gathering"
        else:
            # All params present, go directly to confirming or executing
            self.conversation_stage = "confirming"

    def add_param(self, key: str, value: Any) -> None:
        """Add a collected parameter.

        Args:
            key: Parameter name
            value: Parameter value
        """
        self.gathered_params[key] = value

        # Remove from missing lists
        if key in self.missing_required:
            self.missing_required.remove(key)
        if key in self.missing_recommended:
            self.missing_recommended.remove(key)

    def set_question(self, question: str, param: str | None = None) -> None:
        """Set the current question being asked.

        Args:
            question: The question text
            param: The parameter this question is about
        """
        self.last_question = question
        self.last_question_param = param

    def is_gathering_required(self) -> bool:
        """Check if we're still gathering required params."""
        return bool(self.missing_required)

    def is_gathering_recommended(self) -> bool:
        """Check if we're gathering recommended params."""
        return not self.missing_required and bool(self.missing_recommended)

    def get_next_missing_param(self) -> str | None:
        """Get the next parameter to ask about.

        Required params take priority over recommended.

        Returns:
            Parameter name or None if all collected
        """
        if self.missing_required:
            return self.missing_required[0]
        if self.missing_recommended:
            return self.missing_recommended[0]
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for MongoDB storage.

        Returns:
            Dictionary representation of the state
        """
        return {
            "current_task": self.current_task,
            "original_request": self.original_request,
            "conversation_stage": self.conversation_stage,
            "gathered_params": self.gathered_params,
            "missing_required": self.missing_required,
            "missing_recommended": self.missing_recommended,
            "last_question": self.last_question,
            "last_question_param": self.last_question_param,
            "task_ids": self.task_ids,
            "error": self.error,
            "params_history": self.params_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AgentState":
        """Create AgentState from dictionary (MongoDB document).

        Args:
            data: Dictionary from MongoDB or None

        Returns:
            AgentState instance
        """
        if not data:
            return cls()

        return cls(
            current_task=data.get("current_task"),
            original_request=data.get("original_request"),
            conversation_stage=data.get("conversation_stage", "idle"),
            gathered_params=data.get("gathered_params", {}),
            missing_required=data.get("missing_required", []),
            missing_recommended=data.get("missing_recommended", []),
            last_question=data.get("last_question"),
            last_question_param=data.get("last_question_param"),
            task_ids=data.get("task_ids", []),
            error=data.get("error"),
            params_history=data.get("params_history", []),
        )

    def __repr__(self) -> str:
        return (
            f"AgentState(stage={self.conversation_stage}, "
            f"task={self.current_task}, "
            f"params={len(self.gathered_params)}, "
            f"missing_req={len(self.missing_required)}, "
            f"missing_rec={len(self.missing_recommended)})"
        )
