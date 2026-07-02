# 📊 데일리 마켓 리포트 자동화

매일 장 마감 후 자동으로 실행되어 **텔레그램 + 노션**으로 리포트를 발행합니다.
PC를 켜둘 필요 없이 **GitHub Actions**(무료)에서 클라우드로 실행됩니다.

## 리포트 내용
- **데일리** (평일 17:10 KST): 섹터 ETF 30종 차트(MA5/20/60) + 정배열 판정, 고객예탁금/신용잔고, 거래대금 상위, 상한가, 투자자별 매매동향, 52주 신고가
- **주간** (금요일): ETF 주간 수익률 랭킹
- **월간** (월말): ETF 월간 수익률 랭킹

---

## 설치 순서 (약 20~30분)

### 1단계. GitHub 레포 만들기
1. https://github.com 가입 (무료)
2. New repository → 이름 예: `market-report` → **Private** 선택 → Create
3. 이 폴더의 파일 전체를 업로드
   - 웹에서: "uploading an existing file" 클릭 후 전체 드래그
   - 주의: `.github/workflows/market-report.yml` 경로가 유지되어야 함 (웹 업로드 시 폴더째 드래그하면 유지됨)

### 2단계. KRX 정보데이터시스템 계정 (필수)
pykrx 라이브러리가 KRX 데이터를 받으려면 로그인이 필요합니다.
1. http://data.krx.co.kr 회원가입 (무료)
2. 아이디/비밀번호를 기억해두기 → 4단계에서 Secrets로 등록

### 3단계. 텔레그램 봇 만들기 (5분)
1. 텔레그램에서 `@BotFather` 검색 → `/newbot` → 봇 이름/아이디 지정
2. 발급된 **봇 토큰** 복사 (예: `1234567:ABC-DEF...`)
3. 만든 봇에게 아무 메시지나 하나 보내기
4. 브라우저에서 `https://api.telegram.org/bot<봇토큰>/getUpdates` 접속
   → `"chat":{"id": 123456789}` 부분의 숫자가 **CHAT_ID**

### 4단계. 노션 연동 (10분)
1. https://www.notion.so/my-integrations → New integration → 이름 지정 → **Internal Integration Token** 복사
2. 노션에서 새 페이지 → `/database` 로 **데이터베이스(전체 페이지)** 생성
   - 제목 속성 이름은 `이름` 또는 `Name` 그대로 두면 됨
3. 데이터베이스 페이지 우측 상단 `...` → **연결(Connections)** → 방금 만든 integration 추가
4. 데이터베이스 URL에서 ID 복사:
   `https://notion.so/워크스페이스/<이_32자리가_DATABASE_ID>?v=...`

### 5단계. GitHub Secrets 등록
레포 → Settings → Secrets and variables → **Actions** → New repository secret 으로 아래 6개 등록:

| Secret 이름 | 값 |
|---|---|
| `KRX_ID` | KRX 정보데이터시스템 아이디 |
| `KRX_PW` | KRX 비밀번호 |
| `TELEGRAM_BOT_TOKEN` | 3단계 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 3단계 chat id |
| `NOTION_TOKEN` | 4단계 integration token |
| `NOTION_DATABASE_ID` | 4단계 32자리 ID |

### 6단계. 테스트 실행
레포 → **Actions** 탭 → `Daily Market Report` → **Run workflow** 버튼으로 수동 실행.
몇 분 뒤 텔레그램/노션에 리포트가 도착하면 성공. 이후엔 평일 17:10(KST)에 자동 실행됩니다.

---

## 커스터마이징
- **ETF 목록 변경**: `config.py`의 `ETF_GROUPS` 수정. 이름은 KRX 상장명과 비슷하게만 적으면 자동으로 티커를 찾습니다. 못 찾으면 실행 로그에 `[경고] ETF 못 찾음`이 표시됩니다.
- **실행 시각 변경**: `.github/workflows/market-report.yml`의 cron 수정 (UTC 기준, KST−9시간)
- **수동 실행 모드**: `python main.py weekly` / `python main.py monthly`

## 알아두면 좋은 점 & 한계
- **고객예탁금(금투협)**: 비공식 API를 사용하므로 사이트 개편 시 동작이 멈출 수 있습니다. 실패해도 리포트 나머지 부분은 정상 발행되고 "수집 실패"로 표기됩니다. (`collectors.py`의 `collect_deposits` 수정)
- **52주 신고가**: 네이버금융 페이지를 파싱합니다. 마찬가지로 페이지 구조 변경 시 수정이 필요할 수 있습니다.
- **노션 차트 이미지**: 차트 PNG를 레포에 커밋하고 그 raw URL을 임베드하는 방식이라 **레포가 Public이어야 노션에서 이미지가 보입니다.** Private 레포를 원하면 노션에는 텍스트만 발행되고 차트는 텔레그램으로만 받는 것을 권장합니다.
- **EVENT & ISSUE**: 뉴스 요약은 자동화 대상에서 제외했습니다 (수동 작성 영역).
- GitHub Actions 무료 한도(Private 레포 월 2,000분)는 이 작업(하루 ~5분)에 충분합니다. Public 레포는 무제한.

## 첫 실행에서 흔한 오류
- `KRX 로그인 실패` → `KRX_ID`/`KRX_PW` Secret 오타 확인
- 텔레그램 무반응 → 봇에게 먼저 메시지를 보냈는지, CHAT_ID 확인
- 노션 401/404 → integration을 데이터베이스에 "연결" 했는지 확인
