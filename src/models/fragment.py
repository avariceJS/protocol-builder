from dataclasses import dataclass, field
from enum import Enum
from typing import List, Any


class FragmentStatus(Enum):
    SUCCESS = "Успешно"
    NEEDS_REVIEW = "Нужна проверка"
    NOT_FOUND = "Фрагмент не найден"
    ERROR = "Ошибка"


@dataclass
class Fragment:
    file_path: str
    original_number: str
    assigned_number: str
    status: FragmentStatus
    confidence: int
    xml_nodes: List[Any] = field(default_factory=list)
    text_preview: str = ""
    warnings: List[str] = field(default_factory=list)
    error_message: str = ""
    include_in_protocol: bool = True
    source_type: str = "docx"
