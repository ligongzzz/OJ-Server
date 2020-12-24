import requests
from bs4 import BeautifulSoup
import os

allUniv = []


def getHTMLText(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except:
        return ""


def fillUnivList(soup):
    data = soup.find_all('tr')
    for tr in data:
        ltd = tr.find_all('td')
        if len(ltd) == 0:
            continue
        singleUniv = []
        for i in range(len(ltd)):
            if i == 2:
                singleUniv.append(ltd[i].find('a').string)
            elif i == 3:
                singleUniv.append(ltd[i].find('span').string)
            else:
                singleUniv.append(ltd[i].string)
        allUniv.append(singleUniv)