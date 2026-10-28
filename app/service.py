from collections import defaultdict
from pathlib import Path
from typing import Iterator

from .models import Budget, Transaction
from .repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from .utils import (
    generate_transaction_id,
    validate_amount,
    validate_date,
    validate_date_range,
    validate_month,
    validate_type,
)


class BudgetService:
    """가계부의 업무 로직을 담당한다."""

    DEFAULT_CATEGORIES = [
        "food",
        "transport",
        "rent",
        "shopping",
        "salary",
        "etc",
    ]

    def __init__(
        self,
        data_dir: str = "data",
    ):
        data_path = Path(data_dir)

        data_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.transactions = TransactionRepository(
            data_path / "transactions.jsonl"
        )

        self.categories = CategoryRepository(
            data_path / "categories.jsonl"
        )

        self.budgets = BudgetRepository(
            data_path / "budgets.jsonl"
        )

        self._initialize_categories()

    def _initialize_categories(self) -> None:
        """카테고리 파일이 비어 있으면 기본 카테고리를 생성한다."""

        if not self.categories.all():

            self.categories.replace_all(
                self.DEFAULT_CATEGORIES.copy()
            )

    # --------------------------------------------------
    # Transaction
    # --------------------------------------------------

    def add_transaction(
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: int,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> str:
        """거래를 추가한다."""

        if not validate_date(date):
            raise ValueError(
                "날짜 형식이 올바르지 않습니다. "
                "예: 2026-09-25"
            )

        if not validate_type(transaction_type):
            raise ValueError(
                "타입은 income 또는 expense만 가능합니다."
            )

        if not validate_amount(amount):
            raise ValueError(
                "금액은 0보다 큰 양의 정수여야 합니다."
            )

        if category not in self.categories.all():
            raise ValueError(
                f"등록되지 않은 카테고리입니다: {category}"
            )

        transaction = Transaction(
            id=generate_transaction_id(),
            type=transaction_type,
            date=date,
            category=category,
            amount=amount,
            memo=memo.strip(),
            tags=tags or [],
        )

        self.transactions.add(transaction)

        return transaction.id

    def stream_transactions(
        self,
    ) -> Iterator[Transaction]:
        """
        거래를 최신순으로 스트리밍한다.

        transactions.jsonl 자체가 최신순으로 유지되므로
        별도의 list 정렬이 필요하지 않다.
        """
        yield from self.transactions.stream()

    def list_transactions(
        self,
        limit: int = 10,
    ) -> Iterator[Transaction]:
        """최신 거래를 limit개까지 스트리밍한다."""

        if limit <= 0:
            raise ValueError(
                "--limit은 1 이상의 정수여야 합니다."
            )

        count = 0

        for transaction in self.stream_transactions():

            if count >= limit:
                break

            yield transaction
            count += 1

    def search(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        """
        거래를 조건 검색한다.

        전체 결과를 list로 만들지 않고
        조건에 맞는 거래를 하나씩 yield한다.
        """

        validate_date_range(
            date_from,
            date_to,
        )

        if transaction_type:
            if not validate_type(transaction_type):
                raise ValueError(
                    "--type은 income 또는 expense만 가능합니다."
                )

        if category:
            if category not in self.categories.all():
                raise ValueError(
                    f"등록되지 않은 카테고리입니다: {category}"
                )

        for transaction in self.stream_transactions():

            if date_from:
                if transaction.date < date_from:
                    continue

            if date_to:
                if transaction.date > date_to:
                    continue

            if category:
                if transaction.category != category:
                    continue

            if transaction_type:
                if transaction.type != transaction_type:
                    continue

            if query:
                if query.lower() not in transaction.memo.lower():
                    continue

            if tag:
                if tag not in transaction.tags:
                    continue

            yield transaction

    def update_transaction(
        self,
        transaction_id: str,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """거래를 수정한다."""

        transactions = self.transactions.all()

        target = None

        for transaction in transactions:
            if transaction.id == transaction_id:
                target = transaction
                break

        if target is None:
            return False

        if date is not None:
            if not validate_date(date):
                raise ValueError(
                    "날짜 형식은 YYYY-MM-DD여야 합니다."
                )

            target.date = date

        if transaction_type is not None:
            if not validate_type(transaction_type):
                raise ValueError(
                    "타입은 income 또는 expense만 가능합니다."
                )

            target.type = transaction_type

        if category is not None:
            if category not in self.categories.all():
                raise ValueError(
                    f"등록되지 않은 카테고리입니다: {category}"
                )

            target.category = category

        if amount is not None:
            if not validate_amount(amount):
                raise ValueError(
                    "금액은 0보다 큰 양의 정수여야 합니다."
                )

            target.amount = amount

        if memo is not None:
            target.memo = memo

        if tags is not None:
            target.tags = tags

        # 날짜가 변경될 수 있으므로 다시 최신순으로 정렬한다.
        transactions.sort(
            key=lambda item: (
                item.date,
                item.id,
            ),
            reverse=True,
        )

        self.transactions.replace_all(
            transactions
        )

        return True

    def delete_transaction(
        self,
        transaction_id: str,
    ) -> bool:
        """거래를 삭제한다."""

        transactions = self.transactions.all()

        filtered = [
            transaction
            for transaction in transactions
            if transaction.id != transaction_id
        ]

        if len(filtered) == len(transactions):
            return False

        self.transactions.replace_all(
            filtered
        )

        return True

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(
        self,
        month: str,
        top: int = 3,
    ) -> dict:
        """월별 요약을 계산한다."""

        if not validate_month(month):
            raise ValueError(
                "월은 YYYY-MM 형식이어야 합니다."
            )

        if top <= 0:
            raise ValueError(
                "--top은 1 이상의 정수여야 합니다."
            )

        income = 0
        expense = 0

        category_totals: dict[str, int] = defaultdict(int)

        has_data = False

        for transaction in self.transactions.stream():

            if not transaction.date.startswith(
                month
            ):
                continue

            has_data = True

            if transaction.type == "income":
                income += transaction.amount

            elif transaction.type == "expense":
                expense += transaction.amount

                category_totals[
                    transaction.category
                ] += transaction.amount

        if not has_data:
            return {
                "empty": True,
                "income": 0,
                "expense": 0,
                "balance": 0,
                "top_categories": [],
                "budget": None,
            }

        top_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:top]

        return {
            "empty": False,
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "top_categories": top_categories,
            "budget": self.budgets.get(month),
        }

    # --------------------------------------------------
    # Budget
    # --------------------------------------------------

    def set_budget(
        self,
        month: str,
        amount: int,
    ) -> None:
        """월별 예산을 설정한다."""

        if not validate_month(month):
            raise ValueError(
                "월은 YYYY-MM 형식이어야 합니다."
            )

        if not validate_amount(amount):
            raise ValueError(
                "예산은 0보다 큰 양의 정수여야 합니다."
            )

        self.budgets.save(
            Budget(
                month=month,
                amount=amount,
            )
        )

    # --------------------------------------------------
    # Category
    # --------------------------------------------------

    def list_categories(self) -> list[str]:
        """카테고리 목록을 반환한다."""
        return sorted(
            self.categories.all()
        )

    def add_category(
        self,
        name: str,
    ) -> None:
        """카테고리를 추가한다."""

        name = name.strip()

        if not name:
            raise ValueError(
                "카테고리명을 입력하세요."
            )

        if "\n" in name or "\r" in name:
            raise ValueError(
                "카테고리명에 줄바꿈을 사용할 수 없습니다."
            )

        if name in self.categories.all():
            raise ValueError(
                "이미 존재하는 카테고리입니다."
            )

        self.categories.add(name)

    def remove_category(
        self,
        name: str,
    ) -> bool:
        """카테고리를 삭제한다."""

        categories = self.categories.all()

        if name not in categories:
            return False

        # 현재 거래에서 사용 중인지 확인한다.
        for transaction in self.transactions.stream():
            if transaction.category == name:
                raise ValueError(
                    f"'{name}' 카테고리는 현재 거래에서 "
                    "사용 중이므로 삭제할 수 없습니다."
                )

        remaining = [
            category
            for category in categories
            if category != name
        ]

        self.categories.replace_all(
            remaining
        )

        return True