from __future__ import annotations

from collections.abc import Callable

from ...core.schemas import TaskCategory, WorkflowTemplate
from .data_pipeline import build_template as data_pipeline_template
from .game import build_template as game_template
from .library import build_template as library_template
from .web_app import build_template as web_app_template

TemplateBuilder = Callable[[], WorkflowTemplate]

TEMPLATES: dict[TaskCategory, TemplateBuilder] = {
    TaskCategory.WEB_APPLICATION: web_app_template,
    TaskCategory.DATA_PIPELINE: data_pipeline_template,
    TaskCategory.GAME: game_template,
    TaskCategory.LIBRARY: library_template,
}

__all__ = ["TEMPLATES", "TemplateBuilder"]
