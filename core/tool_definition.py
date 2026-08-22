from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ToolResult:
    success: bool
    output: Any
    error: Optional[str] = None


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.LOW

    def execute(self, **kwargs) -> ToolResult:
        """Executes the tool function and encapsulates the output or error."""
        try:
            res = self.func(**kwargs)
            return ToolResult(success=True, output=res)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))