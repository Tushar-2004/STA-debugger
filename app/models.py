from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TimingPath(BaseModel):
    startpoint: str
    endpoint: str
    clock: str
    path_type: str
    data_arrival_time: Optional[float] = None
    data_required_time: Optional[float] = None
    slack: Optional[float] = None
    status: str
    logic_chain: List[Dict[str, Any]]

class AnalysisSuggestion(BaseModel):
    fix: str
    priority: str  # high, medium, low
    explanation: str

class ViolationAnalysis(BaseModel):
    startpoint: str
    endpoint: str
    path_type: str
    status: str
    slack: Optional[float] = None
    root_cause: Optional[str] = None
    severity: Optional[str] = None
    suggestions: Optional[List[AnalysisSuggestion]] = None
    estimated_effort: Optional[str] = None

class AnalysisReport(BaseModel):
    timestamp: str
    total_paths: int
    violated_paths: int
    analyses: List[ViolationAnalysis]
    summary: Dict[str, Any]