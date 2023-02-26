# -*-coding:utf-8 -*-
import logging
import os
import sys
import time
import traceback

import requests

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S ")

env_key = "LT_MONITOR_COOKIE"


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


def get_envs(env_key):
    if env_key in os.environ:
        configs = os.environ[env_key]
        if len(configs) > 0:
            try:
                return configs
            except Exception as e:
                logging.error(f"{env_key}变量格式错误: {e}")
                sys.exit(1)

        else:
            logging.info(f"{env_key}变量量未启用")
            sys.exit(1)
    else:
        logging.info(f'未添加{env_key}变量')
        sys.exit(1)


# 监控单个
def do_monitor(index, cookie):
    notify_msg = ''
    notify_msg += f'===== 第{index}个账号 =====\n'

    resp = get_diff(cookie=cookie, reset=0)

    if not resp:
        notify_msg += f'获取跳点接口异常了'
        return notify_msg

    code = resp.get('code')
    msg = resp.get('msg')
    data = resp.get('data')

    threshold = float(5)
    if code != 0:
        notify_msg += f"跳点接口业务异常: {msg}"
        return notify_msg
    else:
        diff = float(data.get('diff'))

        if diff > threshold:
            # 通知两次
            for i in [1, 2]:
                send(f'联通跳点监控预警({i}/2)', get_notify_msg(data, threshold))
            # 重置跳点
            get_diff(cookie=cookie, reset=1)

    notify_msg += get_notify_msg(data, threshold)
    return notify_msg


# 获取跳点
def get_diff(cookie, reset=0):
    body = {'cookie': cookie, 'reset': reset}
    try:
        resp = requests.post("http://ipv4.500error.cn:30000/ap/lt/diff", json=body).json()
        return resp
    except Exception as e:
        logging.error(f"获取跳点接口响应异常: {e}")
        return


def get_notify_msg(data, threshold=5):
    diff = float(data.get('diff'))
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return f'发生跳点: {diff}MB \n\n' \
           f'阈值: {threshold}MB \n' \
           f'手机: {data.get("phoneNumber")} \n' \
           f'套餐: {data.get("pkgName")} \n' \
           f'总用: {data.get("sum")}MB \n' \
           f'通用: {data.get("pkg").get("generic")}MB \n' \
           f'定向: {data.get("pkg").get("direction")}MB \n' \
           f'公免: {data.get("free")}MB \n' \
           f'跳点: {data.get("diff")}MB \n' \
           f'上次跳点时间: {data.get("lastTime")} \n' \
           f'当前跳点时间: {time_str} \n\n' \
           f'**注意:** \n' \
           f'套餐流量为：总用 = 通用 + 定向；\n' \
           f'公免为掌厅等免费流量, 跳点仅统计通用流量 \n'


if __name__ == '__main__':

    # 加载通知
    load_send()

    # 获取环境变量
    cookies = get_envs(env_key)

    # 监控
    index = 1
    msg = ''
    for cookie in cookies.split("&"):
        msg += do_monitor(index, cookie)
        msg += "\n\n"
        index += 1

    # 打印信息
    logging.info(msg)
