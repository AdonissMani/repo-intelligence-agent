from dataclasses import dataclass

@dataclass
class ServiceRecord:
    id: str
    owner: str = "Repayment"
