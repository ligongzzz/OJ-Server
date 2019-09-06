import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time
import queue

chromeStarted: bool = False


def submit_code(browser, username: str, password: str, problem_to_solve: str):
    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    browser = webdriver.Chrome(options=option)

    try:
        print("正在获取代码......")
        browser.get(
            'https://raw.githubusercontent.com/ligongzzz/SJTU-OJ/master/Code/Project'
            + problem_to_solve + '/Project' + problem_to_solve + '/源.cpp')
        print('代码获取成功！')
        code_to_input = browser.find_element_by_xpath('/html/body/pre').text
        print(code_to_input)

        browser.get("https://acm.sjtu.edu.cn/OnlineJudge")
        input_username = browser.find_element(By.NAME, 'username')
        input_password = browser.find_element(By.NAME, 'password')
        btn_login = browser.find_element(By.NAME, 'action')

        actions = ActionChains(browser)
        actions.send_keys_to_element(input_username, username)
        actions.send_keys_to_element(input_password, password)
        actions.click(btn_login)
        actions.perform()

        browser.get("https://acm.sjtu.edu.cn/OnlineJudge/submit")

        input_problem = browser.find_element(By.NAME, 'problem')
        input_code = browser.find_element(By.NAME, 'code')
        btn_submit = browser.find_element(
            By.XPATH, '//*[@id="wrap"]/div/form/fieldset/div[4]/button')

        actions = ActionChains(browser)
        actions.send_keys_to_element(input_problem, problem_to_solve)
        actions.send_keys_to_element(input_code, code_to_input)
        actions.click(btn_submit)
        actions.perform()
        browser.quit()
        print('提交已经成功')
        return True
    except:
        print('抱歉！出现错误')
        browser.quit()
        return False


class user_type:
    def __init__(self, username: str, password: str, code: str):
        self.username = username
        self.password = password
        self.code = code


# User Queue
userqueue = queue.Queue()

# Browser
option = webdriver.ChromeOptions()
option.add_argument('--headless')
option.add_argument('--no-sandbox')
browser = webdriver.Chrome(options=option)

print('已经启动提交chrome')
chromeStarted = True


def add_to_queue(username: str, password: str, code: str):
    new_user = user_type(username, password, code)
    userqueue.put(new_user)


def start_service():
    print('提交服务已经开启')
    while True:
        if not userqueue.empty() and chromeStarted:
            nxt: user_type = userqueue.get()
            submit_code(browser, nxt.username, nxt.password, nxt.code)
        else:
            time.sleep(0.2)
