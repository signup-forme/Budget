import sys
import time
from functools import wraps
from typing import Any, Callable


def command_guard(
    func: Callable[..., int],
) -> Callable[..., int]:
    """
    CLI 명령어 공통 처리 데코레이터.

    - 예외 처리
    - 실행 시간 측정
    - 오류 메시지 출력
    - 비정상 종료 코드 반환
    """

    @wraps(func)
    def wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> int:

        start = time.perf_counter()

        try:
            return func(*args, **kwargs)

        except ValueError as exc:
            print(
                f"[오류] {exc}",
                file=sys.stderr,
            )
            print(
                "[힌트] 입력값을 확인한 뒤 다시 실행하세요.",
                file=sys.stderr,
            )
            return 1

        except FileNotFoundError as exc:
            print(
                f"[오류] 파일을 찾을 수 없습니다: {exc}",
                file=sys.stderr,
            )
            print(
                "[힌트] 파일 경로를 확인하세요.",
                file=sys.stderr,
            )
            return 1

        except OSError as exc:
            print(
                f"[오류] 파일 처리 중 문제가 발생했습니다: {exc}",
                file=sys.stderr,
            )
            print(
                "[힌트] 저장 폴더와 파일 권한을 확인하세요.",
                file=sys.stderr,
            )
            return 1

        except Exception as exc:
            print(
                f"[오류] 예상하지 못한 문제가 발생했습니다: {exc}",
                file=sys.stderr,
            )
            print(
                "[힌트] 입력값과 저장 파일을 확인하세요.",
                file=sys.stderr,
            )
            return 1

        finally:
            elapsed = (
                time.perf_counter() - start
            )

            print(
                f"[LOG] 실행시간: {elapsed:.4f}s",
                file=sys.stderr,
            )

    return wrapper