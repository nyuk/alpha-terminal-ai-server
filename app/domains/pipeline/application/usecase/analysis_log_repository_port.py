from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse


class AnalysisLogRepositoryPort(ABC):
    @abstractmethod
    def save_all(self, logs: List[AnalysisLogResponse], account_id: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def find_latest_per_symbol(self, source_types: List[str], account_id: Optional[int] = None) -> List[AnalysisLogResponse]:
        pass

    @abstractmethod
    def find_recent(self, limit: int = 50, account_id: Optional[int] = None) -> List[AnalysisLogResponse]:
        pass
