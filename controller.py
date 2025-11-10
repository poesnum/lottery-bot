import os
import sys
import random
from dotenv import load_dotenv

import auth
import lotto645
import win720
import notification
import time


def buy_lotto645(authCtrl: auth.AuthController, cnt: int, mode: str):
    lotto = lotto645.Lotto645()
    _mode = lotto645.Lotto645Mode[mode.upper()]
    response = lotto.buy_lotto645(authCtrl, cnt, _mode)
    response['balance'] = lotto.get_balance(auth_ctrl=authCtrl)
    return response

def check_winning_lotto645(authCtrl: auth.AuthController) -> dict:
    lotto = lotto645.Lotto645()
    item = lotto.check_winning(authCtrl)
    return item

def buy_win720(authCtrl: auth.AuthController, username: str):
    pension = win720.Win720()
    response = pension.buy_Win720(authCtrl, username)
    response['balance'] = pension.get_balance(auth_ctrl=authCtrl)
    return response

def check_winning_win720(authCtrl: auth.AuthController) -> dict:
    pension = win720.Win720()
    item = pension.check_winning(authCtrl)
    return item

def send_message(mode: int, lottery_type: int, response: dict, webhook_url: str, username: str = None):
    notify = notification.Notification()

    if mode == 0:
        if lottery_type == 0:
            notify.send_lotto_winning_message(response, webhook_url, username)
        else:
            notify.send_win720_winning_message(response, webhook_url, username)
    elif mode == 1:
        if lottery_type == 0:
            notify.send_lotto_buying_message(response, webhook_url, username)
        else:
            notify.send_win720_buying_message(response, webhook_url, username)

def check():
    load_dotenv()

    # 서버 부하 분산을 위한 랜덤 딜레이 (0~300초, 즉 0~5분)
    # 많은 사용자가 동시에 사용해도 트래픽이 분산됩니다
    random_delay = random.randint(0, 300)
    print(f"[서버 부하 분산] {random_delay}초 후 당첨 확인 시작... (DDoS 방지)")
    time.sleep(random_delay)

    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    discord_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')

    globalAuthCtrl = auth.AuthController()
    globalAuthCtrl.login(username, password)

    response = check_winning_lotto645(globalAuthCtrl)
    send_message(0, 0, response=response, webhook_url=discord_webhook_url, username=username)

    time.sleep(10)

    response = check_winning_win720(globalAuthCtrl)
    send_message(0, 1, response=response, webhook_url=discord_webhook_url, username=username)

def buy():

    load_dotenv()

    # 서버 부하 분산을 위한 랜덤 딜레이 (0~300초, 즉 0~5분)
    # 많은 사용자가 동시에 사용해도 트래픽이 분산됩니다
    random_delay = random.randint(0, 300)
    print(f"[서버 부하 분산] {random_delay}초 후 구매 시작... (DDoS 방지)")
    time.sleep(random_delay)

    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    count = int(os.environ.get('COUNT'))
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    discord_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')

    # 전략 모드 선택 (환경변수로 설정 가능)
    # AUTO: 완전 자동
    # SUPERSTITION: 미신 전략 (지난주 구매번호 제외 + 당첨번호 고정)
    mode = os.environ.get('LOTTO_STRATEGY', 'AUTO').upper()

    print(f"[구매 시작] 사용자: {username}, 전략 모드: {mode}")

    globalAuthCtrl = auth.AuthController()
    globalAuthCtrl.login(username, password)

    response = buy_lotto645(globalAuthCtrl, count, mode)
    send_message(1, 0, response=response, webhook_url=discord_webhook_url, username=username)

    time.sleep(10)

    response = buy_win720(globalAuthCtrl, username)
    send_message(1, 1, response=response, webhook_url=discord_webhook_url, username=username)

def run():
    if len(sys.argv) < 2:
        print("Usage: python controller.py [buy|check]")
        return

    if sys.argv[1] == "buy":
        buy()
    elif sys.argv[1] == "check":
        check()
  

if __name__ == "__main__":
    run()
