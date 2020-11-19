# -*- coding: utf-8 -*-
import sys
reload(sys)
import time
from collections import OrderedDict
from urlparse import urljoin
import pymssql
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


def login():
    global driver

    driver.get('https://www.arrow.com/en/login?gotoSplash=true&url=')
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


def findCategoryUrl():

    global driver

    first_url = "https://www.arrow.com/en/products"
    driver.get(first_url)
    time.sleep(3)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    cg_url_list = bs.select("li.CategoryListings-subItems-item > a")
    for url in cg_url_list:

        cg_url = urljoin("https://www.arrow.com", url.get('href'))
        driver.get(cg_url)
        time.sleep(3)

        html = driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        lis = bs.select("ol.SearchResults-pagination > li")
        if len(lis) == 0:
            findProductUrl(cg_url)
        else:
            idx = len(lis) - 2
            max_page = lis[idx].text.strip()
            page = int(max_page) + 1
            for i in range(1, page):
                page_url = cg_url + '?page=' + str(i)
                findProductUrl(page_url)


def findProductUrl(url):

    global driver

    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    pd_url_list = bs.select("td.SearchResults-column.SearchResults-column--name > a")

    for url in pd_url_list:
        pd_url = "https://www.arrow.com" + url.get('href')
        urlParse(pd_url)


def urlParse(url):

    global driver, product_list, product_step_list, db, cursor
    print url

    driver.get(url)
    time.sleep(10)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    product_data = dict()

    #site
    try :
        product_data['SITE'] = 'Arrow'
    except Exception as e :

        product_data['SITE'] = 'Arrow'
        print e
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
        pd_stock = pd_stock.replace(",","")
        product_data['stock_qty'] = int(pd_stock)

    except Exception as e:
        product_data['stock_qty'] = None
        print e

    # 제품정보 : 제조사, 카테고리, 설명
    p = bs.select("p.Product-Summary-Details")
    try:
        product_data['mfg'] = p[0].text.strip()

    except Exception as e:
        product_data['mfg'] = None
        print e

    # description
    try:
        product_data['description'] = p[2].text.strip()

    except Exception as e:
        product_data['description'] = None
        print e

    # 데이터시트
    try:
        sheet = bs.select('div.DatasheetViewer')
        for link in sheet[0].find_all('a'):
            datasheet = "http:" + link.get('href')
            product_data['datesheet_url'] = datasheet
    except Exception as e:
        product_data['datesheet_urlt'] = None
        print e

    # UP
    try:
        up = bs.select_one('span.BuyingOptions-total-newPrice').text.split('$')
        product_data['up'] = float(up[1])
    except Exception as e:
        product_data['up'] = None
        print e

    flag = False
    try:
        sql = '''
        					SELECT * FROM PRODUCT_ITEM
        					WHERE pn = '%s' AND stock_qty = '%d' AND SITE = 'Arrow'
        					''' % (product_data['pn'], product_data['stock_qty'])
    except Exception as e:
        print e
        sql = '''
        					SELECT * FROM PRODUCT_ITEM
        					WHERE pn = '%s' AND stock_qty IS NULL AND SITE = 'Arrow'
        					''' % (product_data['pn'])

    cursor.execute(sql)
    row = cursor.fetchone()
    if row is None:
        product_list.append(product_data)
        insertDatas('PRODUCT_ITEM', product_list)
        del product_list[:]
        flag = True

    # STEP, STEP_UP
    qty = bs.select('span[class*="BuyingOptions-priceTiers-quantity ng-star-inserted"]')
    price = bs.select('span[class*="BuyingOptions-priceTiers-newPrice"]')
    size = len(qty)

    if len(price) == 0:
        del price
        price = bs.select('span[class*="BuyingOptions-priceTiers-price ng-star-inserted"]')

    if (size >= 2) and (flag is True):

        sql = "select max(idx) as idx from PRODUCT_ITEM where SITE = 'Arrow'"
        cursor.execute(sql)
        row = cursor.fetchone()
        if row[0] is None :
            idx = 1
        else:
            idx = row[0]

        qty_list = list()
        price_list = list()
        for i in range(0, size) :
            try:
                qty_list.append(qty[i].text.strip().split('+')[0])
            except Exception as e:
                qty_list.append(None)
                print e

            try:
                price_list.append(price[i].text.strip().split('$')[1])
            except Exception as e:
                price_list.append(None)
                print e

        for i in range(0, size):
            product_step_data = dict()
            try:
                product_step_data['PRODUCT_IDX'] = idx
            except Exception as e:
                product_step_data['PRODUCT_IDX'] = None
                print e
            product_step_data['STEP'] = qty_list[i]
            product_step_data['STEP_UP'] = price_list[i]
            print product_step_data
            product_step_list.append(product_step_data)

        insertDatas('PRODUCT_STEP_ITEM', product_step_list)
        del product_step_list[:]

def insertDatas(table, product_data):

    global db, cursor
    for item in product_data:
        placeholders = ', '.join(['%s'] * len(item))  # %s
        columns = ', '.join(item.keys())  # table 속성list
        sql = "insert into %s ( %s ) values ( %s )" % (table, columns, placeholders)
        # table = table명 columns = table 속성list placeholders = %s %s %s %s...
        try:
            cursor.execute(sql, tuple(item.values()))  # 입력
            db.commit()
        except Exception as e:
            db.rollback()
            print 'rollback ', e


if __name__ == "__main__":

    global driver, product_list, product_step_list, db, cursor

    sys.setdefaultencoding('utf-8')

    product_list = list()
    product_step_list = list()

    driver = webdriver.Chrome('C:\chromedriver_win32\chromedriver.exe')
    driver.implicitly_wait(3)

    db = pymssql.connect(server='121.78.116.145', user='intern', password='intern_2019', database='INTERN')
    cursor = db.cursor()

    login()
    findCategoryUrl()

    db.close()
    print 'success'