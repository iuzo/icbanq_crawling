# -*- coding: utf-8 -*-

import sys
reload(sys)
import datetime
import unicodedata
import requests
import json
import io
from urlparse import *
from bs4 import BeautifulSoup
from collections import OrderedDict


def search_url(search_keyword):
    if len(search_keyword) < 3:
        print("Minimum of 3 characters required to perform the search.")
        sys.exit(1)

    else:

        url = "https://www.richardsonrfpd.com/Products/Search?searchBox=" + str(search_keyword) + "&instockonly=false"
        result = requests.get(url)
        bs = BeautifulSoup(result.content, "html.parser")
        print(url)

        page_flag = bs.select_one("#SearchResultsDiv > div.row > div.col-md-8 > p > strong")
        if not page_flag:
            print("prdouct_page")
            productPageSearch(url)

        else:
            print("list_page")
            num = 1
            flag = True

            while flag:
                flag = listPageSearch(url, num)
                num = num + 1


def listPageSearch(url, page):
    page_url = url.split('?')
    url = page_url[0] + "?page=" + str(page) + "&" + page_url[1]
    print url
    result = requests.get(url)
    bs = BeautifulSoup(result.content, "html.parser")

    tables = bs.findAll("table", {"class": "table table-bordered table-hover table-striped"})
    for table in tables:
        a_tag = table.select('a[href*="Products/Product"]')
        idx = 0
        for i in range(0, len(a_tag) / 2):
            href = a_tag[idx].get('href')
            url = urljoin("https://www.richardsonrfpd.com", href)

            productPageSearch(url)
            idx += 2

    page_list = bs.find("li", {"class": "PagedList-skipToNext"})

    if not page_list:

        print("page finish")
        return False

    else:
        return True


def productPageSearch(url):
    global product_list, all_idx

    product_data = OrderedDict()
    # product_data = dict()
    result = requests.get(url)
    bs = BeautifulSoup(result.content, "html.parser")
    print url

    # 인덱스
    try:
        product_data['idx'] = all_idx
        all_idx += 1
    except Exception as e:
        product_data['idx'] = None
        print e

    # 사이트
    try:
        product_data['SITE'] = 'Richardson'
    except Exception as e:
        product_data['SITE'] = 'Richardson'
        print e
    #img
    try:
        img_url = bs.select_one("div.col-sm-3 > div > img ").get('src')
        img_url = urljoin("https://www.richardsonrfpd.com", img_url)
        # print img_url
        product_data['img_url'] = img_url

    except Exception as e:
        product_data['img_url'] = None
        print e

    # mfg, pn, description
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
            product_data['stock_qty'] = stock

    except Exception as e:
        product_data['stock_qty'] = None

    # 단가
    idx = 0
    name = bs.find(id='PricingTable')
    price = name.select("big")
    pcy_len = len(price) / 2
    if pcy_len == 0:
        product_data["pd_per_stock_0"] = None
        product_data["pd_per_price_0"] = None

    else:
        for i in range(0, pcy_len):
            try:
                qcy = price[idx].text.split(':')
                product_data["pd_per_stock_" + str(i)] = qcy[0]

            except Exception as e:
                product_data["pd_per_stock_" + str(i)] = None
                print e

            try:
                pcy = price[idx + 1].text.split('$')
                product_data["pd_per_price_" + str(i)] = pcy[1]

            except Exception as e:
                product_data["pd_per_price_" + str(i)] = None
                print e

            idx += 2

    product_list.append(product_data)


if __name__ == "__main__":
    global product_data, all_idx

    sys.setdefaultencoding('utf-8')

    product_list = list()
    all_idx = 1
    real_url = raw_input("search keyword :")
    search_url(real_url)

    with io.open(str(real_url)+'_richardson_real.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(product_list, ensure_ascii=False, indent=4)))

    print "success"
