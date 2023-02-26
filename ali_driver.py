import logging
import os
import sys
import traceback

import requests

logging.basicConfig(level=logging.INFO, format='%(message)s')


def load_send() -> None:
    logging.info("加载推送功能中...")
    global send
    send = None
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/../notify.py"):
        try:
            from notify import send
        except Exception:
            send = None
            logging.info(f"❌加载通知服务失败!!!\n{traceback.format_exc()}")
    else:
        logging.info(f"❌加载通知服务失败!!!\n")


def get_configs():
    if "ALI_DRIVER_TOKEN" in os.environ:
        configs = os.environ['ALI_DRIVER_TOKEN']
        if len(configs) > 0:
            try:
                return configs
            except Exception as e:
                logging.error(f"ALI_DRIVER_TOKEN变量格式错误: {e}")
                sys.exit(1)

        else:
            logging.info("ALI_DRIVER_TOKEN量未启用")
            sys.exit(1)
    else:
        send('阿里云盘签到', '未添加ALI_DRIVER_TOKEN变量')
        logging.info("未添加ALI_DRIVER_TOKEN变量")
        sys.exit(0)


def get_access_token(refresh_token):
    url = 'https://auth.aliyundrive.com/v2/account/token'
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    data = {
        "grant_type": "refresh_token",
        "app_id": "pJZInNHN2dZWk8qg",
        "refresh_token": refresh_token
    }
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        json_res = res.json();
        return {
            'access_token': json_res["access_token"],
            'nick_name': json_res['nick_name'],
            'user_name': json_res['user_name']
        }
    return {}


def sign_in(index, refresh_token):
    msg = ''
    msg += f'===== 第{index}个账号({refresh_token}) =====\n'

    # 获取access_token
    info = get_access_token(refresh_token)

    if not info:
        msg += '❌获取access_token失败\n'
    else:
        msg += f"{info['nick_name']}({info['user_name']})开始签到\n"
        if not info:
            logging.info('获取access_token失败')

        headers = {
            "Content-Type": "application/json",
            'Authorization': info['access_token'],
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.2 Safari/605.1.15'
        }
        data = {}
        res = requests.post('https://member.aliyundrive.com/v1/activity/sign_in_list', headers=headers, json=data)
        if res.status_code == 200 and res.json()['success']:
            result = res.json()['result']
            msg += f'🎉第{result["signInCount"]}天签到成功\n\n'

            msg += "当月签到日志:\n"
            for log in result['signInLogs']:
                if log['status'] == 'normal':
                    msg += f'第{log["day"]}天，成功，{log["reward"]["description"]}\n'

    return msg + '\n'


if __name__ == '__main__':
    # 通知
    load_send()
    # 获取环境变量
    refresh_tokens = get_configs()

    msg = ''
    index = 1
    for refresh_token in refresh_tokens.split("&"):
        msg += sign_in(index, refresh_token)
        index += 1

    logging.info(msg)
    send('阿里云盘签到通知', msg)
