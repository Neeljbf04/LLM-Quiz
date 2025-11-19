# modules/schemas.py
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator

ActionLiteral = Literal["fetch", "clean", "visualize", "analyze", "final_answer"]

class FetchArgs(BaseModel):
    url: str
    file_type: Optional[str] = "csv"

class CleanOp(BaseModel):
    op: str
    subset: Optional[List[str]] = None
    cols: Optional[List[str]] = None
    n: Optional[int] = None

class CleanArgs(BaseModel):
    operations: List[CleanOp]

class VisualizeArgs(BaseModel):
    x: str
    y: str
    filename: Optional[str] = None
    caption: Optional[str] = None

class AnalyzeArgs(BaseModel):
    method: str
    n: Optional[int] = None

class FinalArgs(BaseModel):
    message: Optional[str] = None


class PlanStep(BaseModel):
    action: ActionLiteral
    args: Dict[str, Any] = Field(default_factory=dict)

    # Pydantic v2 validator
    @model_validator(mode="after")
    def validate_args(self):
        action = self.action
        args = self.args or {}

        if action == "fetch":
            if "url" not in args:
                raise ValueError("fetch step requires 'url' field")

        if action == "visualize":
            if "x" not in args or "y" not in args:
                raise ValueError("visualize step requires 'x' and 'y' fields")

        # cleaning/analysis are handled in orchestrator
        return self


class Plan(BaseModel):
    steps: List[PlanStep]

    @model_validator(mode="after")
    def validate_steps(self):
        if not self.steps or not isinstance(self.steps, list):
            raise ValueError("Plan must contain a list of steps")
        return self
