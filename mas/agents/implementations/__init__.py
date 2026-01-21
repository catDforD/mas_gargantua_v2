from .backend import descriptor as backend_descriptor
from .code_generation import descriptor as code_generation_descriptor
from .code_review import descriptor as code_review_descriptor
from .data_analysis import descriptor as data_analysis_descriptor
from .frontend import descriptor as frontend_descriptor
from .game_dev import descriptor as game_dev_descriptor
from .planning import descriptor as planning_descriptor

__all__ = [
    "backend_descriptor",
    "code_generation_descriptor",
    "code_review_descriptor",
    "data_analysis_descriptor",
    "frontend_descriptor",
    "game_dev_descriptor",
    "planning_descriptor",
]
