from datetime import datetime
from uuid import uuid4


def validate_date(value: str) -> bool:
    """YYYY-MM-DD 날짜인지 검사한다."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_month(value: str) -> bool:
    """YYYY-MM 형식인지 검사한다."""
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except ValueError:
        return False


def validate_type(value: str) -> bool:
    """거래 타입을 검사한다."""
    return value in {"income", "expense"}


def validate_amount(value: int) -> bool:
    """금액이 양의 정수인지 검사한다."""
    return value > 0


def validate_date_range(
    date_from: str | None,
    date_to: str | None,
) -> None:
    """검색 날짜 범위를 검증한다."""

    if date_from and not validate_date(date_from):
        raise ValueError(
            "--from은 YYYY-MM-DD 형식이어야 합니다."
        )

    if date_to and not validate_date(date_to):
        raise ValueError(
            "--to는 YYYY-MM-DD 형식이어야 합니다."
        )

    if date_from and date_to and date_from > date_to:
        raise ValueError(
            "--from 날짜가 --to 날짜보다 늦을 수 없습니다."
        )


def parse_tags(value: str) -> list[str]:
    """쉼표로 구분된 태그 문자열을 리스트로 변환한다."""
    return [
        tag.strip()
        for tag in value.split(",")
        if tag.strip()
    ]


def generate_transaction_id() -> str:
    """거래용 고유 ID를 생성한다."""
    return f"TX-{uuid4().hex[:12].upper()}"