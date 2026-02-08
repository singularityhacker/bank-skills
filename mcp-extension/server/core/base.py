"""
Base classes and utilities for skill core logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SkillCore(ABC):
    """
    Base class for skill core logic.
    
    All skills should implement this interface to ensure consistency
    across the skill runtime, CLI, web UI, and MCP server.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the skill with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill's main functionality.
        
        Args:
            **kwargs: Skill-specific input parameters
            
        Returns:
            Dictionary containing the skill's output
        """
        pass
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters before execution.
        
        Args:
            **kwargs: Input parameters to validate
            
        Returns:
            True if inputs are valid, False otherwise
        """
        pass
