import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from .models import Budget, Transaction


T = TypeVar("T")


class JsonlRepository:
    """JSONL 파일에 대한 공통 저장 기능."""

    def __init__(self, path: Path):
        self.path = path

        # data 폴더가 없으면 생성한다.
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 파일이 없으면 빈 파일을 생성한다.
        self.path.touch(exist_ok=True)

    def stream(
        self,
        factory: Callable[[dict[str, Any]], T],
    ) -> Iterator[T]:
        """
        JSONL 파일을 한 줄씩 읽는다.

        전체 파일을 list로 읽지 않고 yield를 사용하기 때문에
        제너레이터 기반 스트리밍 처리가 가능하다.
        """

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line_number, line in enumerate(
                file,
                start=1,
            ):
                line = line.strip()

                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield factory(data)

                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise ValueError(
                        f"{self.path.name} "
                        f"{line_number}번째 데이터가 손상되었습니다."
                    ) from exc

    def append(
        self,
        item: T,
        serializer: Callable[[T], dict[str, Any]],
    ) -> None:
        """파일 마지막에 데이터를 추가한다."""
        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:

            json.dump(
                serializer(item),
                file,
                ensure_ascii=False,
            )
            file.write("\n")

    def replace_all(
        self,
        items: Iterator[T] | list[T],
        serializer: Callable[[T], dict[str, Any]],
    ) -> None:
        """
        데이터를 임시 파일에 작성한 뒤 os.replace로 교체한다.

        update/delete에서 기존 파일을 직접 수정하지 않고
        원자적 교체를 사용하기 위한 메서드다.
        """

        fd, temp_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".tmp_",
            suffix=".jsonl",
            text=True,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as file:

                for item in items:
                    json.dump(
                        serializer(item),
                        file,
                        ensure_ascii=False,
                    )
                    file.write("\n")

            os.replace(
                temp_name,
                self.path,
            )

        except Exception:
            if os.path.exists(temp_name):
                os.remove(temp_name)
            raise


class TransactionRepository:
    """거래 데이터 저장소."""

    def __init__(self, path: Path):
        self.repo = JsonlRepository(path)

    def stream(self) -> Iterator[Transaction]:
        """거래 데이터를 스트리밍한다."""
        yield from self.repo.stream(
            Transaction.from_dict
        )

    def all(self) -> list[Transaction]:
        """전체 거래를 리스트로 가져온다."""
        return list(self.stream())

    def add(self, transaction: Transaction) -> None:
        """
        새 거래를 가장 앞에 저장한다.

        파일 자체를 최신순으로 유지하기 때문에
        list/search가 별도의 전체 정렬 없이도
        최신순 스트리밍을 할 수 있다.
        """

        old_transactions = self.stream()

        self.repo.replace_all(
            self._prepend(
                transaction,
                old_transactions,
            ),
            lambda item: item.to_dict(),
        )

    @staticmethod
    def _prepend(
        first: Transaction,
        rest: Iterator[Transaction],
    ) -> Iterator[Transaction]:

        yield first

        for transaction in rest:
            yield transaction

    def replace_all(
        self,
        items: list[Transaction],
    ) -> None:
        """전체 거래를 원자적으로 다시 저장한다."""
        self.repo.replace_all(
            iter(items),
            lambda item: item.to_dict(),
        )


class CategoryRepository:
    """카테고리 저장소."""

    def __init__(self, path: Path):
        self.repo = JsonlRepository(path)

    def stream(self) -> Iterator[str]:
        """카테고리를 스트리밍한다."""
        yield from self.repo.stream(
            lambda data: str(data["name"])
        )

    def all(self) -> list[str]:
        return list(self.stream())

    def add(self, name: str) -> None:
        self.repo.append(
            {"name": name},
            lambda item: item,
        )

    def replace_all(
        self,
        categories: list[str],
    ) -> None:
        self.repo.replace_all(
            iter(
                {"name": category}
                for category in categories
            ),
            lambda item: item,
        )


class BudgetRepository:
    """예산 저장소."""

    def __init__(self, path: Path):
        self.repo = JsonlRepository(path)

    def stream(self) -> Iterator[Budget]:
        """예산을 스트리밍한다."""
        yield from self.repo.stream(
            Budget.from_dict
        )

    def all(self) -> list[Budget]:
        return list(self.stream())

    def get(
        self,
        month: str,
    ) -> Budget | None:

        for budget in self.stream():
            if budget.month == month:
                return budget

        return None

    def save(
        self,
        budget: Budget,
    ) -> None:

        budgets = [
            item
            for item in self.all()
            if item.month != budget.month
        ]

        budgets.append(budget)

        self.repo.replace_all(
            iter(budgets),
            lambda item: item.to_dict(),
        )