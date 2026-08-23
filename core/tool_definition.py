from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Optional
from enum import Enum
import core.tools


class RiskLevel(str, Enum):
    """Defines the security risk level of a tool."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ToolResult:
    """Encapsulates the result of a tool execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None


@dataclass
class ToolDefinition:
    """
    Structured definition for an executable system tool.
    Enforces explicit naming, description, execution function reference, and parameter schema.
    """

    name: str
    description: str
    func: Callable[..., Any]
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters_schema: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters_schema = parameters_schema if parameters_schema is not None else (parameters or {})
        self.risk_level = risk_level

    def execute(self, **kwargs) -> Any:
        """
        Executes the bound tool function with provided parameters.
        Dynamically resolves SystemTools methods to respect mock patches during tests.
        """
        target_func = self.func
        if hasattr(self.func, "__name__") and hasattr(core.tools.SystemTools, self.func.__name__):
            target_func = getattr(core.tools.SystemTools, self.func.__name__)
        return target_func(**kwargs)


# Alias for backward compatibility with older tests
Tool = ToolDefinition