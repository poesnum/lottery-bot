import datetime
import json
import random

from datetime import timedelta
from enum import Enum

from bs4 import BeautifulSoup as BS

import auth
from HttpClient import HttpClientSingleton

class Lotto645Mode(Enum):
    AUTO = 1
    MANUAL = 2
    SUPERSTITION = 3  # 미신 전략 모드
    BUY = 10
    CHECK = 20

class Lotto645:

    _REQ_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        "sec-ch-ua-mobile": "?0",
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://ol.dhlottery.co.kr",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://ol.dhlottery.co.kr/olotto/game/game645.do",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "ko,en-US;q=0.9,en;q=0.8,ko-KR;q=0.7",
    }

    def __init__(self):
        self.http_client = HttpClientSingleton.get_instance()

    def buy_lotto645(
        self,
        auth_ctrl: auth.AuthController,
        cnt: int,
        mode: Lotto645Mode
    ) -> dict:
        assert type(auth_ctrl) == auth.AuthController
        assert type(cnt) == int and 1 <= cnt <= 5
        assert type(mode) == Lotto645Mode

        headers = self._generate_req_headers(auth_ctrl)
        requirements = self._getRequirements(headers)

        if mode == Lotto645Mode.AUTO:
            data = self._generate_body_for_auto_mode(cnt, requirements)
        elif mode == Lotto645Mode.SUPERSTITION:
            data = self._generate_body_for_superstition(auth_ctrl, cnt, requirements)
        else:
            data = self._generate_body_for_manual(cnt)

        body = self._try_buying(headers, data)

        self._show_result(body)
        return body

    def _generate_req_headers(self, auth_ctrl: auth.AuthController) -> dict:
        assert type(auth_ctrl) == auth.AuthController

        return auth_ctrl.add_auth_cred_to_headers(self._REQ_HEADERS)

    def _generate_body_for_auto_mode(self, cnt: int, requirements: list) -> dict:
        assert type(cnt) == int and 1 <= cnt <= 5

        SLOTS = [
            "A",
            "B",
            "C",
            "D",
            "E",
        ]  

        return {
            "round": self._get_round(),
            "direct": requirements[0],  # TODO: test if this can be comment
            "nBuyAmount": str(1000 * cnt),
            "param": json.dumps(
                [
                    {"genType": "0", "arrGameChoiceNum": None, "alpabet": slot}
                    for slot in SLOTS[:cnt]
                ]
            ),
            'ROUND_DRAW_DATE' : requirements[1],
            'WAMT_PAY_TLMT_END_DT' : requirements[2],
            "gameCnt": cnt
        }

    def _generate_body_for_superstition(
        self,
        auth_ctrl: auth.AuthController,
        cnt: int,
        requirements: list
    ) -> dict:
        """
        옵션 C: 혼합 전략
        - 내가 지난주에 구매한 번호는 제외
        - 지난주 당첨번호 중 하나를 각 게임마다 다르게 고정
        - 나머지는 랜덤 선택
        """
        assert type(cnt) == int and 1 <= cnt <= 5

        SLOTS = ["A", "B", "C", "D", "E"]

        # 1. 지난주 구매한 번호 조회 (제외할 번호)
        my_last_numbers = set(self.get_my_last_week_numbers(auth_ctrl))
        print(f"[미신 전략] 지난주 구매 번호 (제외): {sorted(my_last_numbers)}")

        # 2. 지난주 당첨 번호 조회
        current_round = int(self._get_round())
        last_round = current_round - 1
        winning_data = self.get_winning_numbers(last_round)
        winning_pool = winning_data.get("all", [])

        if not winning_pool:
            print("[미신 전략] 당첨번호 조회 실패, AUTO 모드로 대체")
            return self._generate_body_for_auto_mode(cnt, requirements)

        print(f"[미신 전략] 지난주 당첨번호: {winning_pool}")

        # 3. 선택 가능한 번호 풀 (1~45 중 내가 산 번호 제외)
        available_numbers = [n for n in range(1, 46) if n not in my_last_numbers]

        # 4. 각 게임마다 번호 생성
        games = []
        for i in range(cnt):
            # 각 게임마다 다른 당첨번호를 고정
            fixed_number = winning_pool[i % len(winning_pool)]

            # 고정 번호가 제외 리스트에 있어도 포함시킴 (당첨번호니까!)
            if fixed_number not in available_numbers:
                current_pool = available_numbers + [fixed_number]
            else:
                current_pool = available_numbers.copy()

            # 고정번호 1개 + 랜덤 5개 선택
            remaining_pool = [n for n in current_pool if n != fixed_number]

            if len(remaining_pool) < 5:
                print(f"[미신 전략] 선택 가능한 번호 부족, AUTO 모드로 대체")
                return self._generate_body_for_auto_mode(cnt, requirements)

            selected_numbers = [fixed_number] + random.sample(remaining_pool, 5)
            selected_numbers.sort()

            # 동행복권 API는 arrGameChoiceNum을 문자열로 받습니다
            # 예: "7,18,21,22,26,42" (리스트가 아님!)
            games.append({
                "genType": "1",  # 수동 모드
                "arrGameChoiceNum": ",".join(map(str, selected_numbers)),  # ← 문자열로 변환!
                "alpabet": SLOTS[i]
            })

            print(f"[미신 전략] {SLOTS[i]}게임: {selected_numbers} (고정: {fixed_number})")

        return {
            "round": self._get_round(),
            "direct": requirements[0],
            "nBuyAmount": str(1000 * cnt),
            "param": json.dumps(games),
            'ROUND_DRAW_DATE': requirements[1],
            'WAMT_PAY_TLMT_END_DT': requirements[2],
            "gameCnt": cnt
        }

    def _generate_body_for_manual(self, cnt: int) -> dict:
        assert type(cnt) == int and 1 <= cnt <= 5

        raise NotImplementedError()

    def _getRequirements(self, headers: dict) -> list: 
        org_headers = headers.copy()

        headers["Referer"] ="https://ol.dhlottery.co.kr/olotto/game/game645.do"
        headers["Content-Type"] = "application/json; charset=UTF-8"
        headers["X-Requested-With"] ="XMLHttpRequest"


		#no param needed at now
        res = self.http_client.post(
            url="https://ol.dhlottery.co.kr/olotto/game/egovUserReadySocket.json", 
            headers=headers
        )
        
        direct = json.loads(res.text)["ready_ip"]
        

        res = self.http_client.post(
            url="https://ol.dhlottery.co.kr/olotto/game/game645.do", 
            headers=org_headers
        )
        html = res.text
        soup = BS(
            html, "html5lib"
        )
        draw_date = soup.find("input", id="ROUND_DRAW_DATE").get('value')
        tlmt_date = soup.find("input", id="WAMT_PAY_TLMT_END_DT").get('value')

        return [direct, draw_date, tlmt_date]

    def _get_round(self) -> str:
        res = self.http_client.get("https://www.dhlottery.co.kr/common.do?method=main")
        html = res.text
        soup = BS(
            html, "html5lib"
        )  # 'html5lib' : in case that the html don't have clean tag pairs
        last_drawn_round = int(soup.find("strong", id="lottoDrwNo").text)
        return str(last_drawn_round + 1)

    def get_balance(self, auth_ctrl: auth.AuthController) -> str: 

        headers = self._generate_req_headers(auth_ctrl)
        res = self.http_client.post(
            url="https://dhlottery.co.kr/userSsl.do?method=myPage", 
            headers=headers
        )

        html = res.text
        soup = BS(
            html, "html5lib"
        )
        balance = soup.find("p", class_="total_new").find('strong').text
        return balance
        
    def _try_buying(self, headers: dict, data: dict) -> dict:
        assert type(headers) == dict
        assert type(data) == dict

        headers["Content-Type"]  = "application/x-www-form-urlencoded; charset=UTF-8"

        # 디버깅: 요청 데이터 로깅
        print(f"\n[구매 요청] 전송 데이터:")
        for key, value in data.items():
            if key == "param":
                param_preview = str(value)[:300] + "..." if len(str(value)) > 300 else str(value)
                print(f"  {key}: {param_preview}")
            else:
                print(f"  {key}: {value}")

        res = self.http_client.post(
            "https://ol.dhlottery.co.kr/olotto/game/execBuy.do",
            headers=headers,
            data=data,
        )
        res.encoding = "utf-8"

        # 디버깅: 응답 로깅
        print(f"\n[구매 응답] HTTP 상태 코드: {res.status_code}")
        print(f"[구매 응답] Content-Type: {res.headers.get('Content-Type', 'N/A')}")

        # JSON이 아닌 경우 HTML 에러 페이지 전체 출력
        if 'application/json' not in res.headers.get('Content-Type', ''):
            print(f"\n[구매 응답 에러] ⚠️ JSON이 아닌 응답 수신! (서버가 요청을 거부함)")
            print(f"[구매 응답 에러] 응답 전체 내용:")
            print("=" * 80)
            print(res.text)
            print("=" * 80)

        try:
            response_json = json.loads(res.text)
            print(f"[구매 응답] JSON 파싱 성공")
            return response_json
        except json.JSONDecodeError as e:
            print(f"\n[구매 응답 에러] JSON 파싱 실패: {e}")

            # 에러 응답 반환 (알림이 가도록)
            return {
                "loginYn": "Y",
                "result": {
                    "resultMsg": "FAILURE",
                    "failMsg": f"서버가 요청을 거부 (수동 번호 형식 오류 가능)",
                    "serverResponse": res.text[:500]
                }
            }

    def check_winning(self, auth_ctrl: auth.AuthController) -> dict:
        assert type(auth_ctrl) == auth.AuthController

        headers = self._generate_req_headers(auth_ctrl)

        parameters = self._make_search_date()

        data = {
            "nowPage": 1, 
            "searchStartDate": parameters["searchStartDate"],
            "searchEndDate": parameters["searchEndDate"],
            "winGrade": 2,
            "lottoId": "LO40", 
            "sortOrder": "DESC"
        }

        result_data = {
            "data": "no winning data"
        }

        try:
            res = self.http_client.post(
                "https://dhlottery.co.kr/myPage.do?method=lottoBuyList",
                headers=headers,
                data=data
            )

            html = res.text
            soup = BS(html, "html5lib")

            winnings = soup.find("table", class_="tbl_data tbl_data_col").find_all("tbody")[0].find_all("td")

            get_detail_info = winnings[3].find("a").get("href")

            order_no, barcode, issue_no = get_detail_info.split("'")[1::2]
            url = f"https://dhlottery.co.kr/myPage.do?method=lotto645Detail&orderNo={order_no}&barcode={barcode}&issueNo={issue_no}"

            response = self.http_client.get(url)

            soup = BS(response.text, "html5lib")

            lotto_results = []

            for li in soup.select("div.selected li"):
                label = li.find("strong").find_all("span")[0].text.strip()
                status = li.find("strong").find_all("span")[1].text.strip().replace("낙첨","0등")
                nums = li.select("div.nums > span")

                status = " ".join(status.split())

                formatted_nums = []
                for num in nums:
                    ball = num.find("span", class_="ball_645")
                    if ball:
                        formatted_nums.append(f"✨{ball.text.strip()}")
                    else:
                        formatted_nums.append(num.text.strip())

                lotto_results.append({
                    "label": label,
                    "status": status,
                    "result": formatted_nums
                })

            if len(winnings) == 1:
                return result_data

            result_data = {
                "round": winnings[2].text.strip(),
                "money": winnings[6].text.strip(),
                "purchased_date": winnings[0].text.strip(),
                "winning_date": winnings[7].text.strip(),
                "lotto_details": lotto_results
            }
        except:
            pass

        return result_data
    
    def _make_search_date(self) -> dict:
        today = datetime.datetime.today()
        today_str = today.strftime("%Y%m%d")
        weekago = today - timedelta(days=7)
        weekago_str = weekago.strftime("%Y%m%d")
        return {
            "searchStartDate": weekago_str,
            "searchEndDate": today_str
        }

    def get_my_last_week_numbers(self, auth_ctrl: auth.AuthController) -> list:
        """지난주 구매한 모든 번호를 반환 (중복 포함)"""
        assert type(auth_ctrl) == auth.AuthController

        headers = self._generate_req_headers(auth_ctrl)
        parameters = self._make_search_date()

        data = {
            "nowPage": 1,
            "searchStartDate": parameters["searchStartDate"],
            "searchEndDate": parameters["searchEndDate"],
            "winGrade": "",  # 모든 등급
            "lottoId": "LO40",
            "sortOrder": "DESC"
        }

        all_numbers = []

        try:
            res = self.http_client.post(
                "https://dhlottery.co.kr/myPage.do?method=lottoBuyList",
                headers=headers,
                data=data
            )

            html = res.text
            soup = BS(html, "html5lib")

            # 구매 이력 테이블 찾기
            table = soup.find("table", class_="tbl_data tbl_data_col")
            if not table:
                return all_numbers

            # 각 구매 내역 처리
            tbody = table.find("tbody")
            if not tbody:
                return all_numbers

            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                # 상세 정보 링크 추출
                detail_link = cols[3].find("a")
                if not detail_link:
                    continue

                href = detail_link.get("href")
                if not href:
                    continue

                # orderNo, barcode, issueNo 추출
                params = href.split("'")[1::2]
                if len(params) < 3:
                    continue

                order_no, barcode, issue_no = params
                url = f"https://dhlottery.co.kr/myPage.do?method=lotto645Detail&orderNo={order_no}&barcode={barcode}&issueNo={issue_no}"

                response = self.http_client.get(url)
                detail_soup = BS(response.text, "html5lib")

                # 번호 추출
                for li in detail_soup.select("div.selected li"):
                    nums = li.select("div.nums > span")
                    for num in nums:
                        ball = num.find("span", class_="ball_645")
                        if ball:
                            number = int(ball.text.strip())
                            all_numbers.append(number)

        except Exception as e:
            print(f"Error fetching last week numbers: {e}")

        return all_numbers

    def get_winning_numbers(self, round_no: int) -> dict:
        """특정 회차의 당첨 번호 조회"""
        try:
            url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"
            res = self.http_client.get(url)
            data = json.loads(res.text)

            if data.get("returnValue") != "success":
                return {"numbers": [], "bonus": None}

            numbers = [
                int(data.get("drwtNo1", 0)),
                int(data.get("drwtNo2", 0)),
                int(data.get("drwtNo3", 0)),
                int(data.get("drwtNo4", 0)),
                int(data.get("drwtNo5", 0)),
                int(data.get("drwtNo6", 0))
            ]
            bonus = int(data.get("bnusNo", 0))

            return {
                "numbers": numbers,
                "bonus": bonus,
                "all": numbers + [bonus]
            }
        except Exception as e:
            print(f"Error fetching winning numbers: {e}")
            return {"numbers": [], "bonus": None, "all": []}

    def _show_result(self, body: dict) -> None:
        assert type(body) == dict

        print(f"[구매 결과 확인] 전체 응답: {body}")

        if body.get("loginYn") != "Y":
            print(f"[구매 실패] 로그인 상태 아님: loginYn={body.get('loginYn')}")
            return

        result = body.get("result", {})
        result_msg = result.get("resultMsg", "FAILURE").upper()

        if result_msg != "SUCCESS":
            print(f"[구매 실패] resultMsg={result_msg}")
            print(f"[구매 실패] 상세 정보: {result}")

            # 실패 원인 출력
            if "failMsg" in result:
                print(f"[구매 실패] 실패 메시지: {result['failMsg']}")
            if "serverResponse" in result:
                print(f"[구매 실패] 서버 응답: {result['serverResponse']}")

            return

        print(f"[구매 성공] 로또 구매가 완료되었습니다!")
