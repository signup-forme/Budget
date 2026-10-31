# 나만의 용돈 기입장

Python 표준 라이브러리만 사용하여 구현한 파일 기반 콘솔 가계부 프로그램.

## 1. 개발 환경

- Python 3.10 이상
- 외부 라이브러리 사용 없음

## 2. 실행 방법

프로젝트 최상위 폴더에서 실행.

### python -m app --help : 전체 명령어 목록

### python -m app add : 거래 내역 추가

  - 날짜
  - 타입
  - 카테고리
  - 금액
  - 메모
  - 태그

### python -m app list : 거래 목록 조회

- python -m app list --limit (숫자) : 최신순으로 (숫자)만큼 출력

### python -m app search : 거래 내역 검색

  - 기간
``` bash
python -m app search \
  --from 2026-09-01 \
  --to 2026-09-30
```
  - 카테고리
``` bash
python -m app search --category food
```
  - 타입
``` bash
python -m app search --type expense
```
  - 메모
``` bash
python -m app search --q lunch
```
  - 태그
``` bash
python -m app search --tag meal
```

### python -m app summary : 월별 요약

  - 기본
``` bash
python -m app summary \
  --month 2026-09
```
  - 최신순으로 (숫자)만큼 출력
``` bash
python -m app summary \
  --month 2026-09 \
  --top (숫자)
```
- 출력 목록
  - 총수입
  - 총지출
  - 잔액
  - 예산
  - 예산 사용률
  - 예산 초과 여부
  - 카테고리별 지출 TOP (숫자)

### python -m app budget : 예산 관리

EX)
``` bash
python -m app budget set \
  --month 2026-10 \
  --amount 500000
```
→ 2026년 10월에 총 예산 5만원 할당 + 초과 사용 시 summary에서 경고

### python -m app category : 카테고리 관리

사용 중인 카테고리는 삭제 불가 → 기존 거래 데이터의 카테고리가 존재하지 않게 되는 문제를 방지

- 목록
``` bash
python -m app category list
```
- 추가
``` bash
python -m app category add (카테고리 이름)
```
- 삭제
``` bash
python -m app category remove (카테고리 이름)
```

### python -m app update : 거래 수정

입력하지 않은 필드는 기존 값 유지

- 기본
``` bash
python -m app update \
  --id TX-(식별번호)
```
- 다중 수정
``` bash
python -m app update \
  --id TX-(식별번호) \
  --category (변경할 카테고리) \
  --amount (변경값) \
  --memo (변경할 메모) \
  --tags (변경할 태그 1), (변경할 태그 2) ...
```

### python -m app delete : 거래 삭제

존재하지 않는 ID를 입력하면 오류가 아닌 안내 메시지를 출력

``` bash
python -m app delete \
  --id TX-(식별번호)
```

### python -m app export : CSV 내보내기

- 월별
→ --month 필수
``` bash
python -m app export \
  --out export.csv \
  --month 2026-09
```
- 기간 설정
→ --from & --to 필수
``` bash
python -m app export \
  --out export.csv \
  --from 2026-09-01 \
  --to 2026-09-30
```

### python -m app import : CSV 불러오기

``` bash
python -m budget_app import \
  --from import.csv
```

일부 데이터가 잘못된 경우 전체 작업을 중단하지 않고 잘못된 행을 건너뛰며 처리 건수를 출력
``` bash
[완료] imported=8, skipped=2
```

## 3. CSV 스키마

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

## 4. 모듈 구조

### models.py

데이터 구조를 담당

- Transaction
- Budget

### repository.py

파일 입출력을 담당

- JSONL 읽기
- JSONL 쓰기
- 제너레이터 스트리밍
- 원자적 파일 교체

### service.py

가계부 업무 규칙을 담당

- 거래 CRUD
- 검색
- 월별 요약
- 예산
- 카테고리

### cli.py

터미널 명령어와 사용자 입력을 담당

### decorators.py

공통 기능을 담당

- 예외 처리
- 오류 메시지
- 실행 시간 측정

### utils.py

입력 검증 및 공통 유틸리티를 담당

## 5. 제너레이터 스트리밍

`repository.py`의 `stream()`은 JSONL 파일을 한 줄씩 읽고 `yield`한다. 따라서 파일 전체를 메모리에 올리는 것은 아니다. 특히 `list`와 `search`는 결과를 리스트로 변환하지 않고 그대로 순회한다. 이는 거래 데이터가 많아졌을 때 메모리 사용량을 줄일 수 있다는 장점이 있다.

``` bash
for transaction in service.search(...):
    print_transaction(transaction)
```

## 6. update/delete의 안전성

JSONL 파일은 중간의 특정 데이터를 직접 수정하기 극도로 어렵기 때문에, update/delete에서는 다음 과정을 사용하여 데이터를 관리한다. 이를 통해 임시 파일 작성 중 문제가 발생하면 기존 파일을 그대로 지킬 수 있다.

``` bash
기존 파일 읽기
      ↓
임시 파일 생성
      ↓
수정된 전체 데이터 작성
      ↓
os.replace()
      ↓
기존 파일 교체
```

## 7. 데코레이터

`command_guard` 데코레이터는 CLI 실행 함수인 cli.py에 적용하였으며, 공통적으로 다음 기능을 처리한다. 따라서 각 명령어 함수에서 동일한 예외 처리 코드를 반복할 필요가 없다.

- ValueError 처리
- 파일 오류 처리
- 기타 예외 처리
- 오류 원인 출력
- 해결 힌트 출력
- 실행 시간 측정

## 8. JSON VS CSV

저장 포맷은 JSONL으로, 외부 데이터 저장&열가는 CSV import/export 기능으로 구현하였다.

JSONL은 하나의 줄에 하나의 JSON 객체를 저장하기 때문에 파일을 한 줄씩 읽으며, CSV는 쉼표(,)와 줄바꿈(Enter)를 통해 파일을 하나의 표로 저장하여 데이터를 담는다.

JSON이 CSV에 우세하는 점:
- Python 객체 구조를 자연스럽게 저장할 수 있음
- 한 줄씩 읽을 수 있음
- 제너레이터와 호환성이 좋음
- 태그처럼 리스트 형태의 데이터 저장은 편리함
CSV가 JSON에 우세하는 점:
- 한눈에 쉽게 볼 수 있는 가시성 면에서는 CSV가 압도적으로 편리함
- 일부 데이터 수정 시, 수정이 극도로 어려워 파일 전체를 다시 작성해야 하는 JSON과 달리 CSV는 파일로 진입하여 수정할 수 있음

## 9. 오류 처리

CSV를 불러오던 도중 데이터 손상, 잘못된 값 입력 등 프로그램 오류 발생 시 traceback을 사용자에게 노출하지 않는다.

``` bash
[오류] 금액은 0보다 큰 양의 정수여야 합니다.
[힌트] 입력값을 확인한 뒤 다시 실행하세요.
```

정상 종료:
``` bash
exit code 0
```

오류 종료:
``` bash
exit code 1
```

또한, CSV import 과정에서는 모든 행을 무조건 저장하지 않고, 각 행의 유효성을 검사한 다음 성공한 행과 실패한 행을 구분해야 한다.

- 날짜 형식이 YYYY-MM-DD에 맞는지
- 타입이 income 또는 expense인지
- 금액이 양의 정수인지
- 카테고리가 등록되어 있는지
- 필수 컬럼이 존재하는지
- 
오류가 발견되면 행 번호, 오류 원인, 처리 결과를 기록해 사용자가 문제를 쉽게 수정할 수 있도록 한다.

``` bash
[완료] imported=8, skipped=2
```

조금 더 친절한 코드

``` bash
결과
전체 행: 100
성공: 97
실패: 3

실패 내역:
- 12행: 날짜 형식 오류
- 28행: 금액은 양의 정수여야 합니다
- 74행: 등록되지 않은 카테고리입니다
```

## 10. 기타

### 클래스 책임 구조

- `Transaction` : 거래 데이터의 구조를 정의하며, 거래 ID, 날짜, 수입·지출 유형, 금액, 카테고리 등의 필드를 관리한다.
- `TransactionRepository` : 거래 데이터를 파일에 저장하고 읽어오는 역할을 담당하며, 거래 추가, 조회, 수정, 삭제와 같은 파일 입출력을 처리한다.
- `BudgetService` : 월별 수입과 지출을 계산하고 잔액, 카테고리별 지출 합계, 예산 사용률 등을 계산한다.
- `CLI` : 사용자의 명령어와 입력을 받아 적절한 서비스를 호출하고 결과를 화면에 출력한다.

이렇게 나눈 이유는 각 클래스가 하나의 주요 책임에 집중하도록 하기 위함이다. 예를 들어 저장 형식이 JSONL에서 CSV로 바뀌더라도 저장소 부분을 수정하면 되며, 월별 요약 계산 로직도 함께 수정할 필요가 없다. 또한 기능별 테스트를 작성하기 쉽고, 새로운 기능을 추가할 때 기존 코드에 미치는 영향을 줄일 수 있다.

### 타입 힌트

`models.py` 내 최상단 코드이다.

``` bash
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transaction:

    id: str
    type: str
    date: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)
```

이 코드를 아래와 같이 수정한다고 가정한다.

``` bash
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

def iter_transactions() -> Iterator[Transaction]:
    # 거래 파일을 한 건씩 읽어 반환
    yield transaction
```

iter_transactions()는 거래 데이터를 하나씩 반환하는 반복자라는 점과, 반환되는 데이터가 Transaction이라는 점을 타입 힌트로 표현하는데, 이렇게 하면 개발 도구에서 잘못된 타입 사용을 발견하기 쉬워지고, 다른 개발자도 함수의 사용 방법을 빠르게 이해할 수 있다. 예를 들어 amount에 문자열을 넣거나 함수가 예상과 다른 자료형을 반환하면 정적 타입 검사 도구인 mypy 등을 통해 문제를 발견할 수 있다. 그러나 타입 힌트 자체가 실행 중 잘못된 데이터 입력을 자동으로 차단하는 것은 아니므로 실제 입력값에 대해서는 금액이 양수인지, 날짜가 올바른지 등을 별도로 검증해야 한다.

### 거래 내역의 증가

현재 구조가 JSONL 파일을 기반으로 하고 있으므로, 가장 먼저 확인할 병목은 파일 전체를 반복해서 읽는 작업과 검색·정렬 과정이다. 예를 들어 모든 거래를 읽어 리스트로 만든 뒤 최신순으로 정렬하면 거래가 10만 건일 때 메모리 사용량이 증가하고, 정렬에도 추가 비용이 발생한다. 이는 데이터가 많아질수록 메모리를 더 사용한다. 제너레이터를 이용하면 파일을 한 건씩 읽을 수 있어 전체 데이터를 메모리에 올리는 부담을 줄일 수 있다. 하지만 최신순 정렬을 위해 전체 거래를 메모리에 모은다면 그 부분은 여전히 병목이 될 수 있다.

거래가 10만 건 이상으로 증가한다면 다음과 같이 개선할 수 있다.
1. 검색 성능 개선: 날짜나 카테고리별 인덱스를 도입하거나 SQLite 같은 데이터베이스를 사용한다.
2. 요약 성능 개선: 월별 요약 결과를 캐싱하거나 집계 테이블을 활용한다.
3. 안정적인 수정·삭제: 임시 파일에 먼저 기록한 뒤 안전하게 교체하고, 데이터베이스를 사용한다면 트랜잭션을 활용한다.
