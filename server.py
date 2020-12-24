import numpy as np
import threading
import time
import socket
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import submit
import userinfo
import server_utils

# Hyper Parameters
SLEEP_TIME = 5

logging.basicConfig(filename="test.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%M-%Y %H:%M:%S", level=logging.INFO)

# Globle Vars
able_to_exit = False
user_list = []
last_msg_to_send: str = None

# Some Defs


def tcplink(sock: socket.socket, addr):
    print('Accept new connection from', addr)
    logging.info('Accept new user')
    server_utils.send_msg(sock, 'welcome')
    if last_msg_to_send is not None:
        server_utils.send_msg(sock, last_msg_to_send)
    while True:
        try:
            data: bytes = sock.recv(1024)
            print(type(data))
            if len(data) == 0:
                break
            ch_raw = bytes.decode(data, encoding='utf-8')

            while len(ch_raw) != 0:
                try:
                    len_pos = ch_raw.find('~')
                    length = int(ch_raw[:len_pos])
                    ch = ch_raw[len_pos + 1: len_pos + length + 1]
                    ch_raw = ch_raw[len_pos + length + 1:]
                    print(ch)
                    if not ch.startswith('HELLO-CALL'):
                        logging.info("Receive:" + ch)
                    if (ch.startswith("TODO:")):
                        code = ch[5:9]
                        pos = ch.find("~@$")
                        username = ch[9:pos]
                        password = ch[pos+3:]
                        submit.add_to_queue(username, password, code, sock)
                    elif (ch.startswith("HELLO-CALL")):
                        server_utils.send_msg(sock, 'FEEDBACK')
                        print('send: FEEDBACK')
                    elif (ch.startswith("INFO:")):
                        username = ch[5:]
                        userinfo.add_to_queue(username, sock)
                except Exception as err:
                    print(err)
                    print('解析字符串时出错')
                    break
        except:
            break
    server_utils.send_msg(sock, 'toast:服务器即将关闭，请稍后再试')
    time.sleep(2)
    sock.close()
    user_list.remove(sock)
    print('Connection closed.')
    logging.warning('Connection closed.')


def admin_input(s):
    while True:
        op = input()
        print(op)
        if op == 'exit':
            print('即将停止服务...')
            able_to_exit = True
            time.sleep(3)
            s.close()
            submit.end_service()
            time.sleep(10)
            print('所有服务已经结束，您可以退出程序')
            break


def send_msg(msg_to_send: str):
    for sock in user_list:
        try:
            server_utils.send_msg(sock, msg_to_send)
            print('已向用户发送消息')
        except Exception as e:
            print(str(e))
            logging.error(str(e))


def listen_submit():
    last_submit_code = ''
    print('正在启动Chrome......')
    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    browser: webdriver.Chrome = webdriver.Chrome(options=option)
    print('Chrome已开启')

    # 开启提交服务和用户信息采集服务
    threading.Thread(target=submit.start_service).start()
    threading.Thread(target=userinfo.start_service).start()

    browser.get('https://acm.sjtu.edu.cn/OnlineJudge/status#')
    while True:
        try:
            time.sleep(SLEEP_TIME)
            browser.refresh()
            cur_code = browser.find_element(
                By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[1]/a').text
            if cur_code != last_submit_code:
                last_submit_code = cur_code
                print('发现新的提交：', end=' ')
                submit_result: str = None
                while True:
                    submit_result: str = browser.find_element(
                        By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[4]/span').text
                    if submit_result != '未评测' and submit_result != '正在评测' and submit_result != '等待评测':
                        break
                    else:
                        browser.refresh()

                cur_code =  browser.find_element(By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[1]/a').text
                last_submit_code = cur_code
                user_submit: str = browser.find_element(
                    By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[2]').text
                pos_u = user_submit.find(' ')
                user_id = user_submit[:pos_u]
                user_name = user_submit[pos_u+1:]
                problem_to_solve = browser.find_element(
                    By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[3]/a[1]').text

                print('用户是', user_id, '题号是', problem_to_solve)
                msg_to_send = user_name + "!@#" + problem_to_solve + "!@#" + submit_result
                global last_msg_to_send
                last_msg_to_send = msg_to_send
                logging.info('New Submit:'+cur_code)
                threading.Thread(target=send_msg, args=(msg_to_send,)).start()
        except Exception as err:
            logging.error('检测服务异常'+err.__str__())
            print('检测服务出现问题')
            try:
                # browser.close()
                logging.info('关闭Chrome成功')
                print('正在重新启动Chrome......')
                option = webdriver.ChromeOptions()
                option.add_argument('--headless')
                option.add_argument('--no-sandbox')
                browser = webdriver.Chrome(options=option)
                print('Chrome已开启')
                logging.info('Chrome已经重启')
                browser.get('https://acm.sjtu.edu.cn/OnlineJudge/status#')
                logging.info('检测服务重新启动完成')
            except Exception as err_1:
                logging.error('重新启动检测服务异常'+err_1.__str__())

    # Start Listen
print("Start Listen......")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 6666))
logging.info('Server start.')

threading.Thread(target=listen_submit).start()

s.listen(5)
threading.Thread(target=admin_input, args=(s,)).start()

while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    user_list.append(sock)
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()
