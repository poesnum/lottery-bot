import requests
import re

class Notification:
    def send_lotto_buying_message(self, body: dict, webhook_url: str, username: str = None) -> None:
        assert type(webhook_url) == str

        # 사용자 ID 표시 (앞 3자리 + *** 마스킹)
        user_display = ""
        if username:
            masked_id = username[:3] + "***" if len(username) > 3 else username
            user_display = f"👤 **{masked_id}** | "

        result = body.get("result", {})
        result_msg = result.get("resultMsg", "FAILURE").upper()

        # 구매 실패 시 에러 메시지 전송
        if result_msg != "SUCCESS":
            fail_reason = result.get("failMsg", "알 수 없는 오류")
            server_response = result.get("serverResponse", "")

            message = f"{user_display}⚠️ **로또 구매 실패** ⚠️\n"
            message += f"```\n원인: {fail_reason}\n"
            if server_response:
                message += f"서버 응답: {server_response}\n"
            message += "```"

            self._send_discord_webhook(webhook_url, message)
            return

        # 구매 성공 시 정상 메시지
        lotto_number_str = self.make_lotto_number_message(result["arrGameChoiceNum"])
        message = f"{user_display}{result['buyRound']}회 로또 구매 완료 :moneybag: 남은잔액 : {body['balance']}\n```{lotto_number_str}```"
        self._send_discord_webhook(webhook_url, message)

    def make_lotto_number_message(self, lotto_number: list) -> str:
        assert type(lotto_number) == list

        # parse list without last number 3
        lotto_number = [x[:-1] for x in lotto_number]
        
        # remove alphabet and | replace white space  from lotto_number
        lotto_number = [x.replace("|", " ") for x in lotto_number]
        
        # lotto_number to string 
        lotto_number = '\n'.join(x for x in lotto_number)
        
        return lotto_number

    def send_win720_buying_message(self, body: dict, webhook_url: str, username: str = None) -> None:

        # 사용자 ID 표시 (앞 3자리 + *** 마스킹)
        user_display = ""
        if username:
            masked_id = username[:3] + "***" if len(username) > 3 else username
            user_display = f"👤 **{masked_id}** | "

        # 구매 실패 시 에러 메시지 전송
        if body.get("resultCode") != '100':
            result_msg = body.get("resultMsg", "알 수 없는 오류")
            message = f"{user_display}⚠️ **연금복권 구매 실패** ⚠️\n```\n원인: {result_msg}\n```"
            self._send_discord_webhook(webhook_url, message)
            return

        # 구매 성공 시 정상 메시지
        win720_round = body.get("resultMsg").split("|")[3]
        win720_number_str = self.make_win720_number_message(body.get("saleTicket"))

        message = f"{user_display}{win720_round}회 연금복권 구매 완료 :moneybag: 남은잔액 : {body['balance']}\n```\n{win720_number_str}```"
        self._send_discord_webhook(webhook_url, message)

    def make_win720_number_message(self, win720_number: str) -> str:
        formatted_numbers = []
        for number in win720_number.split(","):
            formatted_number = f"{number[0]}조 " + " ".join(number[1:])
            formatted_numbers.append(formatted_number)
        return "\n".join(formatted_numbers)

    def send_lotto_winning_message(self, winning: dict, webhook_url: str, username: str = None) -> None:
        assert type(winning) == dict
        assert type(webhook_url) == str

        try:
            round = winning["round"]
            money = winning["money"]

            max_label_status_length = max(len(f"{line['label']} {line['status']}") for line in winning["lotto_details"])

            formatted_lines = []
            for line in winning["lotto_details"]:
                line_label_status = f"{line['label']} {line['status']}".ljust(max_label_status_length)
                line_result = line["result"]

                formatted_nums = []
                for num in line_result:
                    raw_num = re.search(r'\d+', num).group()
                    formatted_num = f"{int(raw_num):02d}"
                    if '✨' in num:
                        formatted_nums.append(f"[{formatted_num}]")
                    else:
                        formatted_nums.append(f" {formatted_num} ")

                formatted_nums = [f"{num:>6}" for num in formatted_nums]

                formatted_line = f"{line_label_status} " + " ".join(formatted_nums)
                formatted_lines.append(formatted_line)

            formatted_results = "\n".join(formatted_lines)

            # 사용자 ID 표시 (앞 3자리 + *** 마스킹)
            user_display = ""
            if username:
                masked_id = username[:3] + "***" if len(username) > 3 else username
                user_display = f"👤 **{masked_id}** | "

            if winning['money'] != "-":
                winning_message = f"{user_display}로또 *{winning['round']}회* - *{winning['money']}* 당첨 되었습니다 🎉"
            else:
                winning_message = f"{user_display}로또 *{winning['round']}회* - 다음 기회에... 🫠"

            self._send_discord_webhook(webhook_url, f"```ini\n{formatted_results}```\n{winning_message}")
        except KeyError:
            return

    def send_win720_winning_message(self, winning: dict, webhook_url: str, username: str = None) -> None:
        assert type(winning) == dict
        assert type(webhook_url) == str

        try:
            round = winning["round"]
            money = winning["money"]

            # 사용자 ID 표시 (앞 3자리 + *** 마스킹)
            user_display = ""
            if username:
                masked_id = username[:3] + "***" if len(username) > 3 else username
                user_display = f"👤 **{masked_id}** | "

            if winning['money'] != "-":
                message = f"{user_display}연금복권 *{winning['round']}회* - *{winning['money']}* 당첨 되었습니다 🎉"
            else:
                message = f"{user_display}연금복권 *{winning['round']}회* - 다음 기회에... 🫠"

            self._send_discord_webhook(webhook_url, message)
        except KeyError:
            user_display = ""
            if username:
                masked_id = username[:3] + "***" if len(username) > 3 else username
                user_display = f"👤 **{masked_id}** | "
            message = f"{user_display}연금복권 - 다음 기회에... 🫠"
            self._send_discord_webhook(webhook_url, message)
            return

    def _send_discord_webhook(self, webhook_url: str, message: str) -> None:        
        payload = { "content": message }
        requests.post(webhook_url, json=payload)
