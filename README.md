# 🎰 동행복권 자동 구매 봇

동행복권 사이트 계정에 예치금만 넣어두면, 매주 자동으로 **로또 6/45**와 **연금복권 720**을 구매하고 당첨 여부를 확인하여 알려드립니다!

## ✨ 주요 기능

- 🎫 **자동 구매**: 매주 월요일 자동으로 로또 및 연금복권 구매
- 🏆 **당첨 확인**: 자동으로 당첨 여부 확인 및 알림
- 🔔 **Discord 알림**: Discord 웹훅을 통한 실시간 알림
- 🎲 **미신 전략 모드**: 지난주 구매 번호 제외 + 당첨 번호 일부 고정
- ⚙️ **GitHub Actions**: 서버 없이 GitHub에서 자동 실행
- 🔐 **안전한 인증**: GitHub Secrets로 민감 정보 보호

---

## 📊 로또 구매 전략

### 🤖 AUTO 모드 (기본)
- **완전 자동 선택**
- 동행복권 서버가 1~45 중 무작위로 6개 번호 선택
- 가장 단순하고 빠른 방식

```env
LOTTO_STRATEGY=AUTO
```

### 🍀 SUPERSTITION 모드 (미신 전략) ⭐ NEW!

**옵션 C: 혼합 전략**

#### 📋 동작 원리
1. **지난주 구매 번호 조회** → 제외 리스트 생성
2. **지난주 당첨 번호 조회** → 고정 번호 풀 생성
3. **각 게임마다 다른 전략 적용**

#### 🎯 미신 적용
- ❌ **"내가 산 번호는 이번주에 안 나온다"**
  - 지난주에 구매한 모든 번호를 제외
  - 중복 제거하여 제외 리스트 생성

- ✅ **"당첨 번호 중 일부가 다시 나온다"**
  - 지난주 당첨 번호 6개 + 보너스 1개 (총 7개)
  - 각 게임마다 순환하며 1개씩 고정

- 🎲 **나머지는 랜덤 선택**
  - 제외 리스트를 피해서 랜덤하게 5개 선택

#### 📝 예시

**지난주 상황:**
- 구매 번호: `[1, 5, 7, 13, 21, 28, 35, 42, ...]` (30개)
- 당첨 번호: `[3, 12, 18, 25, 33, 41]` + 보너스 `[7]`

**이번주 구매 (5게임):**
```
A게임: [3,  8, 15, 22, 29, 38]  ← 고정: 3  (당첨번호 1번째)
B게임: [4, 12, 17, 23, 31, 40]  ← 고정: 12 (당첨번호 2번째)
C게임: [9, 14, 18, 26, 32, 44]  ← 고정: 18 (당첨번호 3번째)
D게임: [11, 19, 25, 27, 34, 45] ← 고정: 25 (당첨번호 4번째)
E게임: [2, 16, 24, 30, 33, 37]  ← 고정: 33 (당첨번호 5번째)
```

- 모든 게임에서 `[1, 5, 7, 13, 21, 28, 35, 42, ...]` 제외
- 단, 고정 번호가 제외 리스트에 있어도 포함 (당첨번호니까!)

```env
LOTTO_STRATEGY=SUPERSTITION
```

---

## 📁 프로젝트 구조

```
lottery-bot/
├── .github/
│   └── workflows/
│       ├── buy_lotto.yml          # 로또 구매 (월 09:30)
│       ├── buy_lotto_sub.yml      # 로또 구매 서브 (월 09:33)
│       ├── check_winning.yml      # 당첨 확인
│       └── check_winning_sub.yml  # 당첨 확인 서브
├── auth.py                        # 동행복권 로그인/인증
├── HttpClient.py                  # HTTP 요청 싱글톤 클라이언트
├── lotto645.py                    # 로또 6/45 구매/당첨 확인
├── win720.py                      # 연금복권 720 구매/당첨 확인
├── notification.py                # Discord 웹훅 알림
├── controller.py                  # 메인 컨트롤러
├── requirements.txt               # Python 의존성
├── Makefile                       # 빌드 스크립트
└── .env.sample                    # 환경변수 샘플
```

### 핵심 모듈 설명

#### 🔐 `auth.py` - 인증 관리
- 동행복권 로그인 처리
- JSESSIONID 기반 세션 관리
- 인증 헤더 자동 주입

#### 🌐 `HttpClient.py` - HTTP 클라이언트
- 싱글톤 패턴으로 구현
- requests.Session 기반
- 쿠키 자동 관리

#### 🎫 `lotto645.py` - 로또 6/45
**주요 함수:**
- `buy_lotto645()`: 로또 구매
- `check_winning()`: 당첨 확인
- `get_my_last_week_numbers()`: 지난주 구매 번호 조회
- `get_winning_numbers()`: 회차별 당첨 번호 조회
- `_generate_body_for_auto_mode()`: AUTO 모드 요청 생성
- `_generate_body_for_superstition()`: SUPERSTITION 모드 요청 생성

**모드:**
- `AUTO`: 완전 자동 (`genType: "0"`)
- `MANUAL`: 수동 선택 (미구현)
- `SUPERSTITION`: 미신 전략 (`genType: "1"`, 수동 모드 활용)

#### 🎰 `win720.py` - 연금복권 720
- AES 암호화 기반 통신
- PBKDF2 키 유도 함수 사용
- 자동 번호 생성 및 구매

#### 🔔 `notification.py` - 알림
- Discord 웹훅 메시지 전송
- 구매 알림 포맷팅
- 당첨 알림 포맷팅

#### 🎮 `controller.py` - 메인 컨트롤러
**명령어:**
- `python controller.py buy`: 로또 및 연금복권 구매
- `python controller.py check`: 당첨 확인

---

## 🚀 사용법

### 1️⃣ Repository Fork

1. 이 레포지토리를 **Fork** 합니다
2. Fork한 레포지토리로 이동

### 2️⃣ GitHub Secrets 설정

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

#### 필수 환경변수

| Secret 이름 | 설명 | 예시 |
|------------|------|------|
| `USERNAME` | 동행복권 ID (주 계정) | `your_id` |
| `PASSWORD` | 동행복권 비밀번호 (주 계정) | `your_password` |
| `USERNAME_SUB` | 동행복권 ID (서브 계정, 선택) | `your_sub_id` |
| `PASSWORD_SUB` | 동행복권 비밀번호 (서브 계정, 선택) | `your_sub_password` |
| `COUNT` | 구매할 게임 수 (1~5) | `5` |
| `DISCORD_WEBHOOK_URL` | Discord 웹훅 URL | `https://discord.com/api/webhooks/...` |

#### 선택 환경변수

| Secret 이름 | 설명 | 기본값 |
|------------|------|--------|
| `SLACK_WEBHOOK_URL` | Slack 웹훅 URL (미사용) | - |
| `TELEGRAM_BOT_TOKEN` | Telegram 봇 토큰 (미사용) | - |

**참고:** `LOTTO_STRATEGY`는 워크플로우 파일에서 직접 수정합니다.

### 3️⃣ Discord 웹훅 생성

1. Discord 서버 → `서버 설정` → `연동`
2. `웹후크` → `새 웹후크`
3. 웹후크 이름 설정 (예: "로또 봇")
4. 채널 선택
5. `웹후크 URL 복사`
6. GitHub Secrets에 `DISCORD_WEBHOOK_URL`로 등록

### 4️⃣ 전략 모드 선택 (선택 사항)

#### 방법 1: GitHub Actions 워크플로우 수정

`.github/workflows/buy_lotto.yml` 파일 수정:

```yaml
env:
  LOTTO_STRATEGY: SUPERSTITION  # AUTO 또는 SUPERSTITION
```

#### 방법 2: 로컬 .env 파일 (로컬 실행 시)

```bash
# .env 파일 생성
cp .env.sample .env

# .env 파일 수정
LOTTO_STRATEGY=SUPERSTITION
```

### 5️⃣ 동행복권 예치금 충전

1. [동행복권 사이트](https://www.dhlottery.co.kr/) 로그인
2. `마이페이지` → `예치금 관리`
3. 충분한 금액 충전 (로또 1게임 1,000원 × 게임 수 + 연금복권 1,000원)

**권장 예치금:**
- COUNT=5 기준: 6,000원/주 (로또 5,000원 + 연금복권 1,000원)
- 여유있게 50,000원 이상 충전 권장

### 6️⃣ 자동 실행 확인

GitHub Actions가 자동으로 실행됩니다:

- **구매**: 매주 월요일 09:30, 09:33 (KST)
- **당첨 확인**: 매주 토요일 (설정된 시간)

`Actions` 탭에서 실행 로그 확인 가능

---

## 💻 로컬 실행 (테스트용)

### 환경 설정

```bash
# 1. 레포지토리 클론
git clone https://github.com/YOUR_USERNAME/lottery-bot.git
cd lottery-bot

# 2. 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
make install
# 또는
pip3 install -r requirements.txt

# 4. .env 파일 생성
cp .env.sample .env

# 5. .env 파일 수정
nano .env  # 또는 원하는 에디터로 편집
```

### .env 파일 예시

```env
# Default Setup
USERNAME=your_dhlottery_id
PASSWORD=your_password
COUNT=5

# Lotto Strategy
LOTTO_STRATEGY=SUPERSTITION

# For Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
SLACK_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
```

### 실행

```bash
# 로또 구매
make buy
# 또는
python3 controller.py buy

# 당첨 확인
make check
# 또는
python3 controller.py check
```

### 예상 출력

```
[구매 시작] 전략 모드: SUPERSTITION
[미신 전략] 지난주 구매 번호 (제외): [1, 5, 7, 13, 21, 28, 35, 42, ...]
[미신 전략] 지난주 당첨번호: [3, 12, 18, 25, 33, 41, 7]
[미신 전략] A게임: [3, 8, 15, 22, 29, 38] (고정: 3)
[미신 전략] B게임: [4, 12, 17, 23, 31, 40] (고정: 12)
[미신 전략] C게임: [9, 14, 18, 26, 32, 44] (고정: 18)
[미신 전략] D게임: [11, 19, 25, 27, 34, 45] (고정: 25)
[미신 전략] E게임: [2, 16, 24, 30, 33, 37] (고정: 33)
```

---

## 📅 GitHub Actions 스케줄

### 구매 워크플로우

| 워크플로우 | 실행 시간 (KST) | Cron | 설명 |
|----------|----------------|------|------|
| `buy_lotto.yml` | 월요일 09:30 | `30 0 * * 1` | 주 계정 구매 |
| `buy_lotto_sub.yml` | 월요일 09:33 | `33 0 * * 1` | 서브 계정 구매 |

### 당첨 확인 워크플로우

| 워크플로우 | 실행 시간 | 설명 |
|----------|---------|------|
| `check_winning.yml` | 설정된 시간 | 주 계정 당첨 확인 |
| `check_winning_sub.yml` | 설정된 시간 | 서브 계정 당첨 확인 |

**참고:** GitHub Actions의 Cron은 UTC 기준입니다. KST는 UTC+9이므로 `30 0 * * 1` (UTC)는 한국시간 09:30입니다.

### 수동 실행

`Actions` 탭 → 원하는 워크플로우 선택 → `Run workflow`

---

## 🔧 트러블슈팅

### 1. 로그인 실패

**증상:** `로그인에 실패했습니다` 에러

**원인:**
- 잘못된 ID/비밀번호
- 5회 연속 로그인 실패로 계정 잠김
- 동행복권 서버 점검

**해결:**
1. GitHub Secrets의 `USERNAME`, `PASSWORD` 확인
2. 동행복권 사이트에서 직접 로그인 테스트
3. 비밀번호 5회 이상 틀렸다면 비밀번호 재설정
4. 동행복권 공지사항에서 서버 점검 확인

### 2. 예치금 부족

**증상:** 구매 실패, Discord 알림 없음

**해결:**
1. 동행복권 사이트에서 예치금 잔액 확인
2. 충분한 금액 충전 (COUNT × 1,000원 + 1,000원)

### 3. Discord 알림 안옴

**증상:** 구매는 됐는데 알림이 안옴

**원인:**
- 잘못된 웹훅 URL
- Discord 채널 삭제 또는 웹훅 삭제

**해결:**
1. Discord 웹훅 URL 재확인
2. 웹훅이 유효한지 Discord에서 확인
3. `DISCORD_WEBHOOK_URL` Secret 재설정

### 4. SUPERSTITION 모드에서 AUTO로 동작

**증상:** `[미신 전략] 당첨번호 조회 실패, AUTO 모드로 대체`

**원인:**
- 지난주 당첨 번호 조회 API 실패
- 아직 당첨 번호가 발표되지 않음

**해결:**
- 정상 동작입니다. 조회 실패 시 자동으로 AUTO 모드로 대체됩니다.
- 토요일 추첨 후 일요일에 당첨 번호 발표되므로, 월요일 구매 시 정상 동작합니다.

### 5. GitHub Actions 실행 안됨

**증상:** 예정된 시간에 워크플로우가 실행되지 않음

**원인:**
- GitHub Actions 비활성화
- Repository가 Private인 경우 무료 계정 제한
- Fork한 레포지토리의 Actions 기본 비활성화

**해결:**
1. `Actions` 탭 → `I understand my workflows, go ahead and enable them` 클릭
2. Settings → Actions → General → Allow all actions 선택
3. Public 레포지토리 권장 (Private은 무료 계정 제한 있음)

---

## 🔍 API 정보

### 동행복권 API 엔드포인트

#### 로그인
```
POST https://www.dhlottery.co.kr/userSsl.do?method=login
```

#### 로또 6/45 구매
```
POST https://ol.dhlottery.co.kr/olotto/game/execBuy.do
```

#### 연금복권 720 구매
```
POST https://el.dhlottery.co.kr/game/pension720/process/connPro.jsp
```

#### 당첨 번호 조회
```
GET https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={회차}
```

#### 구매 이력 조회
```
POST https://dhlottery.co.kr/myPage.do?method=lottoBuyList
```

#### 잔액 조회
```
POST https://dhlottery.co.kr/userSsl.do?method=myPage
```

---

## 📊 통계 및 분석

### 로또 확률

- **1등**: 1/8,145,060
- **2등**: 1/1,357,510
- **3등**: 1/35,724
- **4등**: 1/733
- **5등**: 1/45

### 미신 전략의 실효성

**과학적 근거:** 없음 😅

로또는 완전한 독립 사건이므로:
- 지난주에 산 번호가 이번주에 나올 확률 = 안 산 번호와 동일
- 지난주 당첨번호가 이번주에 다시 나올 확률 = 다른 번호와 동일

**하지만:**
- 심리적 만족감 제공
- 재미 요소 추가
- "뭔가 하고 있다"는 느낌

---

## ❓ FAQ

### Q1. 여러 계정으로 구매할 수 있나요?
**A.** 네! `buy_lotto.yml` (주 계정)과 `buy_lotto_sub.yml` (서브 계정)을 동시에 사용할 수 있습니다. `USERNAME_SUB`, `PASSWORD_SUB` Secrets를 설정하세요.

### Q2. 구매 시간을 변경할 수 있나요?
**A.** 네. `.github/workflows/buy_lotto.yml` 파일의 cron 표현식을 수정하세요.
```yaml
schedule:
  - cron: '30 0 * * 1'  # UTC 00:30 = KST 09:30
```

### Q3. COUNT를 5개 이상으로 설정할 수 있나요?
**A.** 아니요. 동행복권 API 제한으로 한 번에 최대 5게임까지만 구매 가능합니다.

### Q4. SUPERSTITION 모드에서 고정 번호 개수를 늘릴 수 있나요?
**A.** 현재는 각 게임마다 1개씩 고정됩니다. 코드 수정이 필요합니다. (`lotto645.py:153` 부근)

### Q5. 연금복권도 미신 전략을 적용할 수 있나요?
**A.** 현재는 로또 6/45만 지원합니다. 연금복권은 자동 구매만 가능합니다.

### Q6. Private 레포지토리에서 사용할 수 있나요?
**A.** 네, 하지만 GitHub 무료 계정은 Private 레포지토리의 Actions 실행 시간이 제한됩니다. Public 레포지토리 사용을 권장합니다. (Secrets는 외부에 노출되지 않습니다)

### Q7. 당첨되면 자동으로 수령되나요?
**A.** 아니요. 당첨 확인만 해줍니다. 실제 수령은 동행복권 사이트에서 직접 진행하셔야 합니다.

### Q8. 로또 발행 마감 시간은 언제인가요?
**A.** 매주 토요일 오후 8시까지입니다. 월요일 구매하므로 충분한 여유가 있습니다.

---

## 🛡️ 보안

### GitHub Secrets
- 민감한 정보는 절대 코드에 포함하지 마세요
- 모든 인증 정보는 GitHub Secrets로 관리
- Secrets는 암호화되어 저장되며 로그에 노출되지 않음

### 계정 보안
- 강력한 비밀번호 사용
- 2단계 인증 활성화 (동행복권 지원 시)
- 정기적인 비밀번호 변경

### 코드 보안
- JSESSIONID 기반 세션 관리
- HTTPS 통신
- requests 라이브러리의 검증된 보안 기능 사용

---

## 📝 라이센스

이 프로젝트는 개인 사용 목적으로 제공됩니다.

**주의사항:**
- 동행복권 이용약관을 준수하세요
- 과도한 요청으로 서버에 부하를 주지 마세요
- 상업적 이용 금지
- 책임은 사용자 본인에게 있습니다

---

## 🙏 Credits

- Original API Reference: [roeniss/dhlottery-api](https://github.com/roeniss/dhlottery-api)
- BeautifulSoup4: HTML 파싱
- requests: HTTP 요청
- pycryptodome: 연금복권 암호화

---

## 📞 문의

- Issues: GitHub Issues 탭에 문의해주세요
- 버그 리포트: 상세한 재현 방법과 함께 Issue 등록
- 기능 제안: Feature Request로 Issue 등록

---

## 🎉 행운을 빕니다!

> "로또 1등은 실력이 아니라 운입니다. 하지만 운을 시험해보는 건 자유입니다!" 🍀

**Remember:** 책임감 있는 복권 구매를 하세요. 과도한 구매는 금물!
