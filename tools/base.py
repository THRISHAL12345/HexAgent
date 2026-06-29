from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class ToolResult:
    exit_code: int
    stdout: str
    stderr: str
    parsed: Dict[str, Any]
    artifacts: List[str]
    error: Optional[str]

class Tool(ABC):
    # Required class attributes - defined in each plugin
    name: str = ""
    description: str = ""
    category: str = ""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    requires_root: bool = False
    network_facing: bool = False
    destructive: bool = False

    @abstractmethod
    def run(self, input_args: Dict[str, Any], timeout: int = 300) -> ToolResult:
        """Execute the tool. Return a ToolResult."""
        pass

    def validate_input(self, input_args: Dict[str, Any]) -> None:
        """Schema-validate input before execution."""
        pass

    def parse_output(self, raw: str) -> Dict[str, Any]:
        """Extract structured data from raw output."""
        return {}
