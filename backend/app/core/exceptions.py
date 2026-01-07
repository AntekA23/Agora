from fastapi import HTTPException, status


class AgoraException(Exception):
    """Base exception for Agora application."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentExecutionError(AgoraException):
    """Error during agent execution."""

    def __init__(self, message: str, agent: str):
        super().__init__(message, code="AGENT_EXECUTION_ERROR")
        self.agent = agent


class TaskNotFoundError(AgoraException):
    """Task not found."""

    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} not found", code="TASK_NOT_FOUND")
        self.task_id = task_id


class CompanyNotFoundError(AgoraException):
    """Company not found."""

    def __init__(self, company_id: str):
        super().__init__(f"Company {company_id} not found", code="COMPANY_NOT_FOUND")
        self.company_id = company_id


class UnauthorizedError(AgoraException):
    """Unauthorized access."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")


class RateLimitError(AgoraException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


def raise_not_found(detail: str = "Resource not found"):
    """Raise 404 Not Found exception."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_bad_request(detail: str = "Bad request"):
    """Raise 400 Bad Request exception."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_unauthorized(detail: str = "Unauthorized"):
    """Raise 401 Unauthorized exception."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_forbidden(detail: str = "Forbidden"):
    """Raise 403 Forbidden exception."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
