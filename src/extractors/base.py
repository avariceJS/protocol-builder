from abc import ABC, abstractmethod
from ..models.fragment import Fragment


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> Fragment:
        pass

    @staticmethod
    def calculate_confidence(
        has_start: bool,
        has_table: bool,
        has_proposed: bool,
        has_voting: bool,
        has_decision: bool,
        has_end: bool,
    ) -> int:
        score = 0
        if has_start:    score += 20
        if has_table:    score += 20
        if has_proposed: score += 15
        if has_voting:   score += 15
        if has_decision: score += 15
        if has_end:      score += 15
        return score
