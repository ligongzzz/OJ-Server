import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time
import queue
import socket
import server_utils
import logging

logging.basicConfig(filename="test.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%M-%Y %H:%M:%S", level=logging.INFO)

chromeStarted: bool = False
# Browser
option = webdriver.ChromeOptions()
option.add_argument('--headless')
option.add_argument('--no-sandbox')
browser = webdriver.Chrome(options=option)

print('已经启动提交chrome')
chromeStarted = True


def submit_code(username: str, password: str, problem_to_solve: str, sock: socket.socket):
    global browser
    try:
        # Clear Browser Cookies
        browser.delete_all_cookies()

        print("正在获取代码......")
        browser.get(
                'https://gitee.com/xz2000/SJTU-OJ/raw/master/Code/'+problem_to_solve+'.cpp')
        print('代码获取成功！')
        code_to_input: str = browser.find_element_by_xpath(
            '/html/body/pre').text
        print(code_to_input)

        if (code_to_input.startswith("404:")):
            print('代码获取失败，正在向用户发送信息...')
            logging.error('未找到代码')
            try:
                server_utils.send_msg(sock, "toast:抱歉，服务器没有当前题目的代码")
                print('发送信息成功!')
            except:
                print('向用户发送信息失败！')
            return

        browser.get("https://acm.sjtu.edu.cn/OnlineJudge")
        input_username = browser.find_element(By.NAME, 'username')
        input_password = browser.find_element(By.NAME, 'password')
        btn_login = browser.find_element(By.NAME, 'action')

        actions = ActionChains(browser)
        actions.send_keys_to_element(input_username, username)
        actions.send_keys_to_element(input_password, password)
        actions.click(btn_login)
        actions.perform()

        try:
            browser.get("https://acm.sjtu.edu.cn/OnlineJudge/submit")

            input_problem = browser.find_element(By.NAME, 'problem')
            input_code = browser.find_element(By.NAME, 'code')
            btn_submit = browser.find_element(
                By.XPATH, '//*[@id="wrap"]/div/form/fieldset/div[4]/button')
        except Exception as err:
            logging.error('提交出现异常（账户密码错误）' + err.__str__())
            print('提交出现异常，账户密码错误')
            try:
                server_utils.send_msg(sock, "toast:您的密码有误，请检查您的账户密码")
                print('发送信息成功!')
            except:
                print('向用户发送信息失败！')
            return

        actions = ActionChains(browser)
        actions.send_keys_to_element(input_problem, problem_to_solve)
        actions.send_keys_to_element(input_code, code_to_input)
        actions.click(btn_submit)
        actions.perform()
        print('提交已经成功，正在向用户发送信息')
        logging.info('代码获取成功')
        try:
            server_utils.send_msg(sock, "toast:提交已经成功，请关注评测结果")
            print('发送信息成功!')
        except:
            print('向用户发送信息失败！')
    except Exception as err:
        print('抱歉！出现错误')
        print('正在向用户发送信息...')
        logging.error('代码服务异常' + err.__str__())
        try:
            server_utils.send_msg(sock, "toast:代码提交或拉取服务出现错误，请稍后再试")
            print('发送信息成功!')
        except:
            print('向用户发送信息失败！')
        # Restart Chrome
        # browser.close()
        option = webdriver.ChromeOptions()
        option.add_argument('--headless')
        option.add_argument('--no-sandbox')
        browser = webdriver.Chrome(options=option)
        logging.info('提交服务已经重启')


class user_type:
    def __init__(self, username: str, password: str, code: str, sock: socket.socket):
        self.username = username
        self.password = password
        self.code = code
        self.sock: socket.socket = sock


# User Queue
userqueue = queue.Queue()


def add_to_queue(username: str, password: str, code: str, sock: socket.socket):
    new_user = user_type(username, password, code, sock)
    userqueue.put(new_user)


def start_service():
    print('提交服务已经开启')
    while True:
        if not userqueue.empty() and chromeStarted:
            nxt: user_type = userqueue.get()
            submit_code(nxt.username,
                        nxt.password, nxt.code, nxt.sock)
        else:
            time.sleep(0.2)


def end_service():
    browser.close()
    print('提交服务已经结束')
