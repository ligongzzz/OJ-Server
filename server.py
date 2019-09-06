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

# Hyper Parameters
SLEEP_TIME = 5

logging.basicConfig(filename="test.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%M-%Y %H:%M:%S", level=logging.INFO)

# Globle Vars
able_to_exit = False
user_list = []

# Some Defs


def tcplink(sock, addr):
    print('Accept new connection from', addr)
    logging.info('Accept new user')
    sock.send('welcome'.encode('utf-8'))
    while True:
        try:
            data: bytes = sock.recv(1024)
            print(type(data))
            if len(data) == 0:
                break
            ch = bytes.decode(data, encoding='utf-8')
            print(ch)
            logging.info("Receive:" + ch)
            try:
                if (ch.startswith("TODO:")):
                    code = ch[5:9]
                    pos = ch.find("~@$")
                    username = ch[9:pos]
                    password = ch[pos+3:]
                    submit.add_to_queue(username, password, code)
                    sock.send('submit_success'.encode('utf-8'))
                    print('send: submit_success')
                    logging.info('send: submit_success')
                elif (ch.startswith("HELLO-CALL")):
                    sock.send('FEEDBACK'.encode('utf-8'))
                    print('send: FEEDBACK')
            except:
                sock.send('submit_fail'.encode('utf-8'))
        except:
            break
    sock.send('submit_fail'.encode('utf-8'))
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
            break


def send_msg(msg_to_send: str):
    for sock in user_list:
        try:
            sock.send(msg_to_send.encode('utf-8'))
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
    browser = webdriver.Chrome(options=option)
    print('Chrome已开启')
    threading.Thread(target=submit.start_service).start()

    browser.get('https://acm.sjtu.edu.cn/OnlineJudge/status#')
    while True:
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

            user_submit: str = browser.find_element(
                By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[2]').text
            [user_id, user_name] = user_submit.split()
            problem_to_solve = browser.find_element(
                By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[3]/a[1]').text

            print('用户是', user_id, '题号是', problem_to_solve)
            msg_to_send = user_name + "!@#"+problem_to_solve+"!@#"+submit_result
            logging.info('New Submit:'+cur_code)
            threading.Thread(target=send_msg, args=(msg_to_send,)).start()

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
