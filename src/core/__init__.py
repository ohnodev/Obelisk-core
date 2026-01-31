"""
Core service container and bootstrap module
Provides centralized service initialization and dependency management
"""
from .container import ServiceContainer
from .bootstrap import get_container

__all__ = ["ServiceContainer", "get_container"]
