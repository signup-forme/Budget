import argparse
import csv
from typing import Iterator

from .decorators import command_guard
from .models import Transaction
from .service import BudgetService
from .utils import (
    parse_tags,
    validate_date,
    validate_month,
)


def build_parser() -> argparse.ArgumentParser:
    """CLI argument parser를 생성한다."""

    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="나만의 용돈 기입장 프로그램",
    )

    parser.add_argument(
        "--data-dir",
        default="data",
        help="데이터 저장 폴더 (기본값: data)",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    subparsers.add_parser(
        "add",
        help="거래 추가",
    )

    # --------------------------------------------------
    # list
    # --------------------------------------------------

    list_parser = subparsers.add_parser(
        "list",
        help="거래 목록 조회",
    )

    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="조회할 거래 수 (기본값: 10)",
    )

    # --------------------------------------------------
    # search
    # --------------------------------------------------

    search_parser = subparsers.add_parser(
        "search",
        help="거래 검색",
    )

    search_parser.add_argument(
        "--from",
        dest="date_from",
        help="시작 날짜 YYYY-MM-DD",
    )

    search_parser.add_argument(
        "--to",
        dest="date_to",
        help="종료 날짜 YYYY-MM-DD",
    )

    search_parser.add_argument(
        "--category",
        help="카테고리",
    )

    search_parser.add_argument(
        "--type",
        dest="transaction_type",
        choices=["income", "expense"],
        help="거래 타입",
    )

    search_parser.add_argument(
        "--q",
        help="메모 검색어",
    )

    search_parser.add_argument(
        "--tag",
        help="태그",
    )

    # --------------------------------------------------
    # summary
    # --------------------------------------------------

    summary_parser = subparsers.add_parser(
        "summary",
        help="월별 요약",
    )

    summary_parser.add_argument(
        "--month",
        required=True,
        help="YYYY-MM",
    )

    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="지출 TOP N (기본값: 3)",
    )

    # --------------------------------------------------
    # budget
    # --------------------------------------------------

    budget_parser = subparsers.add_parser(
        "budget",
        help="예산 관리",
    )

    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
    )

    budget_set_parser = budget_subparsers.add_parser(
        "set",
        help="월 예산 설정",
    )

    budget_set_parser.add_argument(
        "--month",
        required=True,
        help="YYYY-MM",
    )

    budget_set_parser.add_argument(
        "--amount",
        type=int,
        required=True,
        help="예산 금액",
    )

    # --------------------------------------------------
    # category
    # --------------------------------------------------

    category_parser = subparsers.add_parser(
        "category",
        help="카테고리 관리",
    )

    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
    )

    category_subparsers.add_parser(
        "list",
        help="카테고리 목록",
    )

    category_add_parser = category_subparsers.add_parser(
        "add",
        help="카테고리 추가",
    )

    category_add_parser.add_argument(
        "name",
        nargs="?",
        help="카테고리명",
    )

    category_remove_parser = category_subparsers.add_parser(
        "remove",
        help="카테고리 삭제",
    )

    category_remove_parser.add_argument(
        "name",
        nargs="?",
        help="카테고리명",
    )

    # --------------------------------------------------
    # update
    # --------------------------------------------------

    update_parser = subparsers.add_parser(
        "update",
        help="거래 수정",
    )

    update_parser.add_argument(
        "--id",
        required=True,
        help="거래 ID",
    )

    update_parser.add_argument(
        "--date",
        help="YYYY-MM-DD",
    )

    update_parser.add_argument(
        "--type",
        choices=["income", "expense"],
        help="income / expense",
    )

    update_parser.add_argument(
        "--category",
        help="카테고리",
    )

    update_parser.add_argument(
        "--amount",
        type=int,
        help="금액",
    )

    update_parser.add_argument(
        "--memo",
        help="메모",
    )

    update_parser.add_argument(
        "--tags",
        help="쉼표로 구분된 태그",
    )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------

    delete_parser = subparsers.add_parser(
        "delete",
        help="거래 삭제",
    )

    delete_parser.add_argument(
        "--id",
        required=True,
        help="거래 ID",
    )

    # --------------------------------------------------
    # export
    # --------------------------------------------------

    export_parser = subparsers.add_parser(
        "export",
        help="CSV 내보내기",
    )

    export_parser.add_argument(
        "--out",
        required=True,
        help="출력 CSV 파일",
    )

    export_parser.add_argument(
        "--month",
        help="YYYY-MM",
    )

    export_parser.add_argument(
        "--from",
        dest="date_from",
        help="시작 날짜 YYYY-MM-DD",
    )

    export_parser.add_argument(
        "--to",
        dest="date_to",
        help="종료 날짜 YYYY-MM-DD",
    )

    # --------------------------------------------------
    # import
    # --------------------------------------------------

    import_parser = subparsers.add_parser(
        "import",
        help="CSV 가져오기",
    )

    import_parser.add_argument(
        "--from",
        dest="source",
        required=True,
        help="입력 CSV 파일",
    )

    return parser


def print_transaction(
    transaction: Transaction,
) -> None:
    """거래 한 건을 출력한다."""

    print(
        f"{transaction.id} | "
        f"{transaction.date} | "
        f"{transaction.type:<7} | "
        f"{transaction.category:<12} | "
        f"{transaction.amount:>10} | "
        f"{transaction.memo}"
    )


def print_transactions(
    transactions: Iterator[Transaction],
) -> int:
    """거래를 스트리밍하면서 출력한다."""

    count = 0

    for transaction in transactions:
        print_transaction(transaction)
        count += 1

    return count


def prompt_category(
    service: BudgetService,
) -> str:
    """대화형 카테고리 입력."""

    categories = service.list_categories()

    print(
        "등록된 카테고리:",
        ", ".join(categories),
    )

    return input("카테고리: ").strip()


def prompt_positive_integer(
    message: str,
) -> int:
    """양의 정수를 대화형으로 입력받는다."""

    value = input(message).strip()

    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(
            "금액은 정수로 입력해야 합니다."
        ) from exc

    if number <= 0:
        raise ValueError(
            "금액은 0보다 큰 양의 정수여야 합니다."
        )

    return number


@command_guard
def run(args: argparse.Namespace) -> int:
    """실제 CLI 명령을 실행한다."""

    service = BudgetService(
        args.data_dir
    )

    # ==================================================
    # add
    # ==================================================

    if args.command == "add":

        date = input(
            "날짜(YYYY-MM-DD): "
        ).strip()

        transaction_type = input(
            "타입(income/expense): "
        ).strip()

        category = prompt_category(
            service
        )

        amount = prompt_positive_integer(
            "금액(양수): "
        )

        memo = input(
            "메모(선택): "
        ).strip()

        tag_input = input(
            "태그(쉼표로 구분, 없으면 엔터): "
        ).strip()

        tags = parse_tags(
            tag_input
        )

        transaction_id = service.add_transaction(
            date=date,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )

        print(
            f"[저장 완료] id={transaction_id}"
        )

        return 0

    # ==================================================
    # list
    # ==================================================

    if args.command == "list":

        count = print_transactions(
            service.list_transactions(
                args.limit
            )
        )

        if count == 0:
            print("데이터 없음")

        return 0

    # ==================================================
    # search
    # ==================================================

    if args.command == "search":

        count = print_transactions(
            service.search(
                date_from=args.date_from,
                date_to=args.date_to,
                category=args.category,
                transaction_type=args.transaction_type,
                query=args.q,
                tag=args.tag,
            )
        )

        if count == 0:
            print("검색 결과 없음")

        return 0

    # ==================================================
    # summary
    # ==================================================

    if args.command == "summary":

        if not validate_month(
            args.month
        ):
            raise ValueError(
                "--month은 YYYY-MM 형식이어야 합니다."
            )

        result = service.summary(
            month=args.month,
            top=args.top,
        )

        if result["empty"]:
            print(
                f"{args.month}: 데이터 없음"
            )
            return 0

        print(
            f"===== {args.month} 월별 요약 ====="
        )

        print(
            f"총 수입: {result['income']:,}원"
        )

        print(
            f"총 지출: {result['expense']:,}원"
        )

        print(
            f"잔액: {result['balance']:,}원"
        )

        budget = result["budget"]

        if budget is not None:

            usage = (
                result["expense"]
                / budget.amount
                * 100
            )

            print(
                f"예산: {budget.amount:,}원"
            )

            print(
                f"예산 사용률: {usage:.1f}%"
            )

            if result["expense"] > budget.amount:
                print(
                    "[경고] 예산을 초과했습니다."
                )

            else:
                print(
                    "[정상] 예산 범위 내에서 사용 중입니다."
                )

        print()
        print(
            f"지출 TOP {args.top}"
        )

        for index, (
            category,
            amount,
        ) in enumerate(
            result["top_categories"],
            start=1,
        ):
            print(
                f"{index}) "
                f"{category}: "
                f"{amount:,}원"
            )

        return 0

    # ==================================================
    # budget
    # ==================================================

    if args.command == "budget":

        if args.budget_command == "set":

            service.set_budget(
                month=args.month,
                amount=args.amount,
            )

            print(
                f"[저장 완료] "
                f"{args.month} 예산 "
                f"{args.amount:,}원"
            )

            return 0

    # ==================================================
    # category
    # ==================================================

    if args.command == "category":

        if args.category_command == "list":

            categories = service.list_categories()

            print("===== 카테고리 =====")

            for category in categories:
                print(f"- {category}")

            return 0

        if args.category_command == "add":

            name = args.name

            if not name:
                name = input(
                    "카테고리명: "
                ).strip()

            service.add_category(name)

            print(
                f"[저장 완료] category={name}"
            )

            return 0

        if args.category_command == "remove":

            name = args.name

            if not name:
                name = input(
                    "삭제할 카테고리명: "
                ).strip()

            removed = service.remove_category(
                name
            )

            if removed:
                print(
                    f"[삭제 완료] category={name}"
                )
            else:
                print(
                    f"[실패] 존재하지 않는 "
                    f"카테고리입니다: {name}"
                )

            return 0

    # ==================================================
    # update
    # ==================================================

    if args.command == "update":

        tags = None

        if args.tags is not None:
            tags = parse_tags(
                args.tags
            )

        updated = service.update_transaction(
            transaction_id=args.id,
            date=args.date,
            transaction_type=args.type,
            category=args.category,
            amount=args.amount,
            memo=args.memo,
            tags=tags,
        )

        if updated:
            print(
                f"[수정 완료] id={args.id}"
            )
        else:
            print(
                f"[실패] 존재하지 않는 "
                f"id={args.id}"
            )

        return 0

    # ==================================================
    # delete
    # ==================================================

    if args.command == "delete":

        deleted = service.delete_transaction(
            args.id
        )

        if deleted:
            print(
                f"[삭제 완료] id={args.id}"
            )
        else:
            print(
                f"[실패] 존재하지 않는 "
                f"id={args.id}"
            )

        return 0

    # ==================================================
    # export
    # ==================================================

    if args.command == "export":

        if args.month:

            if not validate_month(
                args.month
            ):
                raise ValueError(
                    "--month은 YYYY-MM 형식이어야 합니다."
                )

            if args.date_from or args.date_to:
                raise ValueError(
                    "--month과 --from/--to를 "
                    "동시에 사용할 수 없습니다."
                )

            date_from = f"{args.month}-01"
            date_to = f"{args.month}-31"

        else:

            if not (
                args.date_from
                and args.date_to
            ):
                raise ValueError(
                    "export는 --month 또는 "
                    "--from과 --to를 함께 지정해야 합니다."
                )

            date_from = args.date_from
            date_to = args.date_to

        transactions = service.search(
            date_from=date_from,
            date_to=date_to,
        )

        count = 0

        with open(
            args.out,
            "w",
            encoding="utf-8",
            newline="",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "date",
                    "type",
                    "category",
                    "amount",
                    "memo",
                    "tags",
                ],
            )

            writer.writeheader()

            for transaction in transactions:

                writer.writerow(
                    {
                        "date": transaction.date,
                        "type": transaction.type,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "memo": transaction.memo,
                        "tags": ",".join(
                            transaction.tags
                        ),
                    }
                )

                count += 1

        print(
            f"[완료] {args.out} "
            f"({count} records)"
        )

        return 0

    # ==================================================
    # import
    # ==================================================

    if args.command == "import":

        required_columns = {
            "date",
            "type",
            "category",
            "amount",
            "memo",
            "tags",
        }

        imported = 0
        skipped = 0

        with open(
            args.source,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            fieldnames = set(
                reader.fieldnames or []
            )

            missing = required_columns - fieldnames

            required_without_optional = {
                "date",
                "type",
                "category",
                "amount",
            }

            missing_required = (
                required_without_optional
                - fieldnames
            )

            if missing_required:
                raise ValueError(
                    "CSV 필수 컬럼이 없습니다: "
                    + ", ".join(
                        sorted(missing_required)
                    )
                )

            for row in reader:

                try:
                    date = (
                        row.get("date", "")
                        .strip()
                    )

                    transaction_type = (
                        row.get("type", "")
                        .strip()
                    )

                    category = (
                        row.get("category", "")
                        .strip()
                    )

                    amount_text = (
                        row.get("amount", "")
                        .strip()
                    )

                    memo = (
                        row.get("memo") or ""
                    )

                    tag_text = (
                        row.get("tags") or ""
                    )

                    if not date:
                        raise ValueError(
                            "date가 비어 있습니다."
                        )

                    if not transaction_type:
                        raise ValueError(
                            "type이 비어 있습니다."
                        )

                    if not category:
                        raise ValueError(
                            "category가 비어 있습니다."
                        )

                    if not amount_text:
                        raise ValueError(
                            "amount가 비어 있습니다."
                        )

                    amount = int(
                        amount_text
                    )

                    service.add_transaction(
                        date=date,
                        transaction_type=transaction_type,
                        category=category,
                        amount=amount,
                        memo=memo,
                        tags=parse_tags(
                            tag_text
                        ),
                    )

                    imported += 1

                except (
                    ValueError,
                    KeyError,
                ):
                    skipped += 1

        print(
            f"[완료] imported={imported}, "
            f"skipped={skipped}"
        )

        return 0

    return 0


def main() -> int:
    """프로그램 진입점."""

    parser = build_parser()

    args = parser.parse_args()

    return run(args)