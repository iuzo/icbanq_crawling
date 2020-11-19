# -*- coding: utf-8 -*-
# https://www.microchipdirect.com DATA CRAWLING
import sys
reload(sys)
import unicodedata
import lxml
import pymssql
import requests
import lxml.html
from urlparse import *
from bs4 import BeautifulSoup



# from crConfig import *

def urlParse(url):

    global product_list, product_step_list, db, cursor

    result = requests.get(url)
    bs = BeautifulSoup(result.content, "html.parser")
    product_data = dict()
    print url

    # 사이트
    try:
        product_data['SITE'] = 'Richardson'
    except Exception as e :
        product_data['SITE'] = 'Richardson'
        print e

    # img
    try:
        img_url = bs.select_one("div.col-sm-3 > div > img ").get('src')
        img_url = urljoin("https://www.richardsonrfpd.com", img_url)
        # print img_url
        product_data['img_url'] = img_url

    except Exception as e:
        product_data['img_url'] = None
        print e

    # 제조사, 제품명, 설명
    pd_info = list()
    for data in bs.select("div.col-sm-9 > p"):
        pd_data = unicodedata.normalize("NFKD", data.text)
        pd_data = pd_data.split(':')[1].strip()
        pd_info.append(pd_data)

    try:
        product_data['mfg'] = pd_info[0]
    except Exception as e:
        product_data['mfg'] = None
        print e

    try:
        product_data['pn'] = pd_info[1]
    except Exception as e:
        product_data['pn'] = None
        print e

    try:
        product_data['description'] = pd_info[2]
    except Exception as e:
        product_data['description'] = None
        print e

    # 데이타시트 url
    try:
        sheet_url = bs.select_one("div.col-sm-9 > div.well.well-sm > a")
        sheet_url = sheet_url.get('href')
        product_data['datesheet_url'] = sheet_url
    except Exception as e:

        product_data['datesheet_url'] = None
        print e

    # 재고
    try:
        table = bs.find("td", {"class": "text-left"})
        stock = table.text.strip()

        if stock.find('Time') > 0:
            product_data['stock_qty'] = None

        else:
            product_data['stock_qty'] = int(stock)

    except Exception as e:
        product_data['stock_qty'] = " "

    # 단가
    insert_flag = False
    len_flag = False
    name = bs.find(id='PricingTable')
    price = name.select("big")
    pcy_len = len(price)

    try:

        if pcy_len == 0:
            product_data["up"] = None

        elif pcy_len >= 2:
            pcy = price[1].text.split('$')
            product_data['up'] = pcy[1]
            if pcy_len > 2:
                len_flag = True

    except Exception as e:
        product_data["up"] = None
        print e
    try:
        sql = '''
        					SELECT * FROM PRODUCT_ITEM
        					WHERE pn = '%s' AND stock_qty = '%d' AND SITE = 'Richardson'
        					''' % (product_data['pn'], product_data['stock_qty'])
    except Exception as e:
        print e
        sql = '''
        					SELECT * FROM PRODUCT_ITEM
        					WHERE pn = '%s' AND stock_qty IS NULL AND SITE = 'Richardson'
        					''' % (product_data['pn'])

    cursor.execute(sql)
    row = cursor.fetchone()
    if row is None:
        product_list.append(product_data)
        insertDatas('PRODUCT_ITEM', product_list)
        insert_flag = True
        del product_list[:]

    if (insert_flag is True) and (len_flag is True):
        print "step"
        db_idx = fetchIDX()
        findStepItem(url, db_idx)



def fetchIDX() :

    global db, cursor

    sql = "select max(idx) as idx from PRODUCT_ITEM where SITE = 'Richardson'"
    cursor.execute(sql)
    row = cursor.fetchone()
    if row[0] is None :
        return 1
    else:
        return row[0]

def findStepItem(url, pd_idx):

    global product_step_list

    result = requests.get(url)
    bs = BeautifulSoup(result.content, "html.parser")

    idx = 0
    name = bs.find(id='PricingTable')
    price = name.select("big")
    pcy_len = len(price) / 2

    for i in range(0, pcy_len):

        step_data = dict()
        try:
            step_data['PRODUCT_IDX'] = pd_idx
        except Exception as e:
            step_data['PRODUCT_IDX'] = None
        try:
            qcy = price[idx].text.split(':')
            step_data['STEP'] = int(qcy[0])
        except Exception as e:
            step_data['STEP'] = None
            print e
        try:
            pcy = price[idx + 1].text.split('$')
            step_data["STEP_UP"] = float(pcy[1])
        except Exception as e:
            step_data["STEP_UP"] = None
            print e

        idx += 2
        product_step_list.append(step_data)
        insertDatas('product_step_item', product_step_list)
        del product_step_list[:]

def findProductUrl(url, page):
    global product_list, product_step_list

    page_url = url.split('?')
    url = page_url[0] + "?page=" + str(page) + "&" + page_url[1]
    result = requests.get(url)
    bs = BeautifulSoup(result.content, "html.parser")

    tables = bs.findAll("table", {"class": "table table-bordered table-hover table-striped"})
    for table in tables:
        a_tag = table.select('a[href*="Products/Product"]')
        idx = 0
        for i in range(0, len(a_tag) / 2):
            href = a_tag[idx].get('href')
            url = urljoin("https://www.richardsonrfpd.com", href)
            urlParse(url)
            idx += 2

    page_list = bs.find("li", {"class": "PagedList-skipToNext"})
    if not page_list:

        print("cg finish")
        return False

    else:
        return True


def findCategoryUrl(url):
    result = requests.get(url)
    document = lxml.html.fromstring(result.text)

    for a_tag in document.cssselect('ul.dropdown-menu > li > a[href*="endCategory"]'):
        cg_href = a_tag.get('href')
        url = urljoin("https://www.richardsonrfpd.com", cg_href)
        num = 1
        flag = True
        print(url)
        while flag:
            flag = findProductUrl(url, num)
            num = num + 1



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
    sys.setdefaultencoding('utf-8')

    global product_list, product_step_list, db, cursor

    db = pymssql.connect(server='121.78.116.145', user='intern', password='intern_2019', database='INTERN')
    cursor = db.cursor()

    product_list = list()
    product_step_list = list()


    findCategoryUrl("https://www.richardsonrfpd.com/")
    db.close()

    print 'success'
