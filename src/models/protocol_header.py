from dataclasses import dataclass


@dataclass
class ProtocolHeader:
    protocol_number: str = ""
    protocol_date: str = ""
    session_name: str = ""
    organization: str = ""
    participants: str = ""
    secretary: str = ""
    quorum_text: str = ""
    agenda_item: str = ""
