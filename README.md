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

### python -m budget_app export : CSV 내보내기

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
