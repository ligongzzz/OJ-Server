import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time
import queue
import threading
import socket
import server_utils

chromeStarted: bool = False


class info_type:
    def __init__(self, code: str, problem: str, result: str):
        self.code = code
        self.problem = problem
        self.result = result


class user_type:
    def __init__(self, username: str, sock: socket.socket):
        self.username = username
        self.sock = sock


def get_user_info(username: str, sock: socket.socket):
    try:
        # Clear Browser Cookies
        browser.delete_all_cookies()
        user_result = []

        if user_dict.get(username) is not None:
            user_result = user_dict.get(username)
        latest_code = user_latest_submit.get(username)
        cur_latest_code: str = None

        print('开始获取' + username + '的用户信息')
        browser.get(
            'https://acm.sjtu.edu.cn/OnlineJudge/status?owner=' + username + '&problem=&language=0&verdict=0')
        name_user: str = browser.find_element(
            By.XPATH, '//*[@id="status"]/tbody/tr[1]/td[2]').text
        # Check if the first fetch.
        first_fetch = 1
        cnt = 0

        while True:
            try:
                flag = False
                for i in range(first_fetch, 16):
                    cur_code = browser.find_element(
                        By.XPATH, '//*[@id="status"]/tbody/tr[' + str(i) + ']/td[1]/a').text
                    if first_fetch and i == 1:
                        cur_latest_code = cur_code
                    if cur_code == latest_code:
                        flag = True
                        break

                    cur_pro = browser.find_element(
                        By.XPATH, '//*[@id="status"]/tbody/tr[' + str(i) + ']/td[3]/a[1]').text
                    cur_result = browser.find_element(
                        By.XPATH, '//*[@id="status"]/tbody/tr[' + str(i) + ']/td[4]/span').text
                    user_result.append(info_type(
                        cur_code, cur_pro, cur_result))
                    cnt += 1
                if flag:
                    break

                if first_fetch == 1:
                    first_fetch = 2

                # Move to another page.
                browser.find_element(
                    By.XPATH, '//*[@id="status"]/tbody/tr[15]/td[1]/a').click()
            except Exception as err:
                print('结束，信息获取完成')
                break

        print('共收集到' + username + '的' + str(cnt) + '次提交，正在发送...')
        problem_set = set()
        problem_solved_set = set()
        submit_cnt = 0
        submit_solved_cnt = 0

        for item in user_result:
            if item.problem not in problem_set:
                problem_set.add(item.problem)
            if item.result == '正确' and item.problem not in problem_solved_set:
                problem_solved_set.add(item.problem)
            submit_cnt += 1
            if item.result == '正确':
                submit_solved_cnt += 1

        to_send: str = ""
        if submit_cnt == 0:
            to_send = "info_fail"
        else:
            pos = name_user.find(' ')
            user = name_user[:pos]
            name = name_user[pos:]
            to_send = "info:" + user + "!#@%!" + name + \
                "!#@%!"+"完成题目    "+str(len(problem_solved_set))+"!#@%!" + \
                "提交记录    "+str(submit_solved_cnt)+"/"+str(submit_cnt) + \
                "({:.2f}%)".format(submit_solved_cnt / submit_cnt*100)
        try:
            server_utils.send_msg(sock, to_send)
            print('信息发送成功！')

            # 存储用户数据
            user_dict[username] = user_result
            np.save('user_dict.npy', user_dict)
            user_latest_submit[username] = cur_latest_code
            np.save('user_latest.npy', user_latest_submit)
            print('保存用户信息成功！')
        except:
            print('信息发送异常！')

    except Exception as err:
        print(err)
        print('信息服务出现异常，可能无此用户！')
        try:
            server_utils.send_msg(sock, 'info_fail')
            print('信息发送成功！')
        except:
            print('信息发送异常！')


# User Queue
userqueue = queue.Queue()

# Browser
option = webdriver.ChromeOptions()
option.add_argument('--headless')
option.add_argument('--no-sandbox')
browser = webdriver.Chrome(options=option)

print('已经启动提交chrome')
chromeStarted = True

# 用户提交数据记录
user_dict = {}
user_latest_submit = {}

# 加载用户信息
try:
    user_dict = np.load('user_dict.npy', allow_pickle=True).item()
    user_latest_submit = np.load('user_latest.npy', allow_pickle=True).item()
except Exception as err:
    print(err)
    print('提取用户信息失败！')


def add_to_queue(username: str, sock: socket.socket):
    userqueue.put(user_type(username, sock))


def start_service():
    print('用户信息服务已经开启')
    while True:
        if not userqueue.empty() and chromeStarted:
            cur_user: user_type = userqueue.get()
            get_user_info(cur_user.username, cur_user.sock)
        else:
            time.sleep(0.2)


def end_service():
    browser.close()
    print('用户信息服务已经结束')
