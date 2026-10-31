# 나만의 용돈 기입장

Python 표준 라이브러리만 사용하여 구현한 파일 기반 콘솔 가계부 프로그램.

## 1. 개발 환경

- Python 3.10 이상
- 외부 라이브러리 사용 없음

## 2. 실행 방법

프로젝트 최상위 폴더에서 실행.

```bash
python -m app --help : 전체 명령어 목록

python -m app add : 거래 내역 추가
> 날짜
> 타입
> 카테고리
> 금액
> 메모
> 태그

python -m app list : 거래 목록 조회
python -m app list --limit (숫자) : 최신순으로 (숫자)만큼 출력

python -m app search : 거래 내역 검색
> 기간
>> python -m app search \
     --from 2026-09-01 \
     --to 2026-09-30
> 카테고리
>> python -m app search --category food
> 타입
>> python -m app search --type expense
> 메모
>> python -m app search --q lunch
> 태그
>> python -m app search --tag meal

python -m app summary : 월별 요약
> 기본
>> python -m app summary \
     --month 2026-09
> 최신순으로 (숫자)만큼 출력
>> python -m app summary \
     --month 2026-09 \
     --top (숫자)
> 출력 목록
>> 총수입
>> 총지출
>> 잔액
>> 예산
>> 예산 사용률
>> 예산 초과 여부
>> 카테고리별 지출 TOP (숫자)

python -m budget_app budget : 예산 관리
EX)
python -m budget_app budget set \
  --month 2026-10 \
  --amount 500000
→ 2026년 10월에 총 예산 5만원 할당 + 초과 사용 시 summary에서 경고
