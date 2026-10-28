from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transaction:
    """거래 내역 데이터 모델."""

    id: str
    type: str
    date: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON 저장용 딕셔너리로 변환한다."""
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "category": self.category,
            "amount": self.amount,
            "memo": self.memo,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """딕셔너리를 Transaction으로 변환한다."""
        tags = data.get("tags", [])

        if isinstance(tags, str):
            tags = [
                tag.strip()
                for tag in tags.split(",")
                if tag.strip()
            ]

        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            date=str(data["date"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            memo=str(data.get("memo", "")),
            tags=list(tags),
        )


@dataclass
class Budget:
    """월별 예산 데이터 모델."""

    month: str
    amount: int

    def to_dict(self) -> dict[str, Any]:
        """JSON 저장용 딕셔너리로 변환한다."""
        return {
            "month": self.month,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        """딕셔너리를 Budget으로 변환한다."""
        return cls(
            month=str(data["month"]),
            amount=int(data["amount"]),
        )