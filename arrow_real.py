# -*- coding: utf-8 -*-
import sys
reload(sys)
import datetime
import io
import json
import time
from collections import OrderedDict
from urlparse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

def search_url(search_keyword):

    global driver

    if len(search_keyword) < 2:
        print("Minimum of 2 characters required to perform the search.")
        sys.exit(1)

    else:

        page_url = "https://www.arrow.com/en/products/search?cat=&q=" + str(search_keyword) + "&r=true"
        driver.get(page_url)
        time.sleep(3)

        html = driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        flag = bs.select_one("#jumpToProducts > div > div.Layout-Search-Filters > div.FilterCategoryNavigation > div.SearchBreadcrumbs > ul > li")
        print flag

        if flag is None :
            print "page"
            url = "https://www.arrow.com/en/products/" + str(search_keyword) + "/analog-devices"
            urlParse(url)

        else :
            print "list"
            print page_url
            lis = bs.select("ol.SearchResults-pagination > li")
            if len(lis) == 0:
                findProductUrl(page_url)
            else:
                idx = len(lis) - 2
                max_page = lis[idx].text.strip()
                page = int(max_page) + 1
                for i in range(1, page):
                    page_url = page_url.split('?')[0] + '?page=' + str(i) + '&q=' + str(search_keyword) + '&cat=&r=true'
                    findProductUrl(page_url)

def findProductUrl(url):

    global driver

    print url
    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    pd_url_list = bs.select("td.SearchResults-column.SearchResults-column--name > a")

    for url in pd_url_list:
        pd_url = urljoin("https://www.arrow.com", url.get('href'))
        urlParse(pd_url)

def urlParse(url):

    global driver, product_list, all_idx

    print url
    driver.get(url)
    time.sleep(5)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    product_data = OrderedDict()
    #인덱스
    try:
        product_data['idx'] = all_idx
        all_idx += 1
    except Exception as e :
        product_data['idx'] = None
        print e

    # 사이트
    try:
        product_data['SITE'] = 'Arrow'
    except Exception as e :
        product_data['SITE'] = 'Arrow'

    # 이름
    try:
        pd_no = bs.select_one("span.product-summary-name__title").text
        product_data['pn'] = pd_no
    except Exception as e:
        product_data['pn'] = None
        print e

    # 이미지 url
    try:
        img_find = bs.find("img", {"class": "Product-Summary-Image"})
        img = (img_find.get('src'))
        product_data['img_url'] = img

    except Exception as e:
        product_data['img_url'] = None
        print e
    # 스톡
    try:
        pd_stock = bs.select_one("li.ng-star-inserted > strong").text.strip()
        pd_stock = pd_stock.split(' ')[0]
        product_data['stock_qcy'] = pd_stock

    except Exception as e:
        product_data['stock_qcy'] = None
        print e

    # 제품정보 : 제조사, 카테고리, 설명
    p = bs.select("p.Product-Summary-Details")
    try:
        product_data['mfg'] = p[0].text.strip()

    except Exception as e:
        product_data['mfg'] = None
        print e

    try:
        product_data['pd_cg'] = p[1].text.strip()

    except Exception as e:
        product_data['pd_cg'] = None
        print e

    try:
        product_data['description'] = p[2].text.strip()

    except Exception as e:
        product_data['description'] = None
        print e

    # 단가
    q_idx = 0
    try :
        qty = bs.select('span[class*="BuyingOptions-priceTiers-quantity ng-star-inserted"]')
        # print(qty)
        temp = qty[0]
        i = 0
        for pd_per_stock in qty:
            if temp == pd_per_stock and i != 0:
                break
            i = i + 1
            per_stock = pd_per_stock.text.strip()
            product_data['pd_per_stock'+str(q_idx)] = per_stock.split('+')[0]
            q_idx += 1

    except Exception as e:
        product_data['pd_per_stock' + str(q_idx)] = None
        print e

    p_idx = 0
    try:
        price = bs.select('span[class*="BuyingOptions-priceTiers-newPrice"]')
        if len(price) == 0 :
            price = bs.select('span[class*="BuyingOptions-priceTiers-price ng-star-inserted"]')

        a = 0
        for pd_per_price in price:
            if a == i:
                break
            a = a + 1
            per_price = pd_per_price.text.strip()
            per_price = per_price.split('$')
            product_data['pd_per_price'+str(p_idx)] = per_price[1]
            p_idx += 1

    except Exception as e:
        product_data['pd_per_price' + str(p_idx)] = None
        print e

    # 데이터시트
    try:
        sheet = bs.select('div.DatasheetViewer')
        for link in sheet[0].find_all('a'):
            datasheet = "http:" + link.get('href')
            product_data['data_sheet'] = datasheet
    except Exception as e:
        product_data['data_sheet'] = None
        print e

    product_list.append(product_data)

def login():

    global driver
    # URL 접근
    driver.get('https://www.arrow.com/en/login?gotoSplash=true&url=')

    # 웹 자원 로드를 위해 암묵적으로 딜레이
    delay_time = 3
    driver.implicitly_wait(delay_time)

    # ID, PW 입력
    id = "cjsales@quantustechnology.com"
    pw = "Quantus3639"
    elem = driver.find_element_by_name('username')
    elem.click()
    elem.click()
    elem.send_keys(id)

    elem = driver.find_element_by_name('password')
    elem.click()
    elem.click()
    elem.send_keys(pw)

    # 로그인 버튼 클릭
    element = driver.find_element_by_xpath('//*[@id="loginForm"]/div[6]/button/span')
    driver.execute_script("arguments[0].click();", element)
    time.sleep(15)



if __name__ == "__main__":

    global driver, product_list, all_idx

    driver = webdriver.Chrome('C:\chromedriver_win32\chromedriver.exe')
    product_list = list()
    all_idx = 1

    login()
    real_url = raw_input("search keyword :")
    search_url(real_url)

    with io.open(str(real_url)+'_arrow_real.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(product_list, ensure_ascii=False, indent=4)))

    print 'success'