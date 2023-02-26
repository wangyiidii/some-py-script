# -*- coding: utf-8 -*
import json
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
    if "MI_STEP" in os.environ:
        configs = os.environ['MI_STEP']
        if len(configs) > 0:
            try:
                return json.loads(configs)
            except Exception as e:
                logging.error(f"MI_STEP变量格式错误: {e}")
                sys.exit(1)

        else:
            logging.info("MI_STEP变量未启用")
            sys.exit(1)
    else:
        send('小米运动刷新步数', '未添加MI_STEP变量')
        logging.info("未添加MI_STEP变量")
        sys.exit(0)


def sign_in(config):
    phone = config.get('phone')
    body = {'phone': phone, 'password': config.get('password'), "step": config.get('step')}
    try:
        res = requests.post("http://ipv4.500error.cn:30000/ap/sign-in/mi-step", json=body).json()
        data = res.get('data')
        msg = ''
        if data == 0:
            msg = phone + res.data
        else:
            msg = phone + ": " + res.get('msg')
        logging.info(msg)
        send('小米运动刷新步数', msg)
    except Exception as e:
        logging.error(f"接口异常: {e}")


if __name__ == '__main__':
    load_send()
    configs = get_configs()
    for config in configs:
        sign_in(config)
