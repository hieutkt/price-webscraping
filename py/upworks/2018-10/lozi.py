from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
import zipfile
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select



SITE_NAME = "lozi"
BASE_URL = "https://lozi.vn"
PROJECT_PATH = os.getcwd()
PROJECT_PATH = PROJECT_PATH.replace("\\",'/')
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CHROME_DRIVER_PATH = "bin/chromedriver"

def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'location', 'seller', 'address', 'price', 'date'))
        writer.writerow((data['category'], data['location'], data['seller'], data['address'], data['price'], data['date']))

def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    chromeOptions.add_argument("--headless")
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,30)
    urls = ['https://lozi.vn/a/ha-noi/photos/do-an', 'https://lozi.vn/a/ha-noi/b', 'https://lozi.vn/a/ha-noi/photos/do-an-ship', 'https://lozi.vn/a/ha-noi/photos/goc-con-gai', 'https://lozi.vn/a/ha-noi/photos/do-con-trai', 'https://lozi.vn/a/ha-noi/photos/my-pham', 'https://lozi.vn/a/ha-noi/photos/do-dien-tu', 'https://lozi.vn/a/ha-noi/photos/do-gia-dung', 'https://lozi.vn/a/ha-noi/photos/me-va-be', 'https://lozi.vn/a/ha-noi/photos/fan-han-quoc', 'https://lozi.vn/a/ha-noi/photos/fan-nhat-ban', 'https://lozi.vn/a/ha-noi/photos/xe-co', 'https://lozi.vn/a/ha-noi/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/ha-noi/photos/sneaker', 'https://lozi.vn/a/ha-noi/photos/toc-spa', 'https://lozi.vn/a/ha-noi/photos/thu-cung', 'https://lozi.vn/a/ha-noi/photos/sach-va-truyen', 'https://lozi.vn/a/ha-noi/photos/do-choi-va-so-thich', 'https://lozi.vn/a/ha-noi/photos/dung-cu-am-nhac', 'https://lozi.vn/a/ha-noi/photos/vat-dung-trang-tri', 'https://lozi.vn/a/ha-noi/photos/nha-phong-tro', 'https://lozi.vn/a/ha-noi/photos/hang-order', 'https://lozi.vn/a/ha-noi/photos/can-mua', 'https://lozi.vn/a/ha-noi/photos/homestay', 'https://lozi.vn/a/ha-noi/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/ha-noi/photos/khac', 'https://lozi.vn/a/ha-noi/photos/quan-tam', 'https://lozi.vn/a/hai-phong/photos/do-an', 'https://lozi.vn/a/hai-phong/b', 'https://lozi.vn/a/hai-phong/photos/do-an-ship', 'https://lozi.vn/a/hai-phong/photos/goc-con-gai', 'https://lozi.vn/a/hai-phong/photos/do-con-trai', 'https://lozi.vn/a/hai-phong/photos/my-pham', 'https://lozi.vn/a/hai-phong/photos/do-dien-tu', 'https://lozi.vn/a/hai-phong/photos/do-gia-dung', 'https://lozi.vn/a/hai-phong/photos/me-va-be', 'https://lozi.vn/a/hai-phong/photos/fan-han-quoc', 'https://lozi.vn/a/hai-phong/photos/fan-nhat-ban', 'https://lozi.vn/a/hai-phong/photos/xe-co', 'https://lozi.vn/a/hai-phong/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/hai-phong/photos/sneaker', 'https://lozi.vn/a/hai-phong/photos/toc-spa', 'https://lozi.vn/a/hai-phong/photos/thu-cung', 'https://lozi.vn/a/hai-phong/photos/sach-va-truyen', 'https://lozi.vn/a/hai-phong/photos/do-choi-va-so-thich', 'https://lozi.vn/a/hai-phong/photos/dung-cu-am-nhac', 'https://lozi.vn/a/hai-phong/photos/vat-dung-trang-tri', 'https://lozi.vn/a/hai-phong/photos/nha-phong-tro', 'https://lozi.vn/a/hai-phong/photos/hang-order', 'https://lozi.vn/a/hai-phong/photos/can-mua', 'https://lozi.vn/a/hai-phong/photos/homestay', 'https://lozi.vn/a/hai-phong/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/hai-phong/photos/khac', 'https://lozi.vn/a/hai-phong/photos/quan-tam', 'https://lozi.vn/a/da-nang/photos/do-an', 'https://lozi.vn/a/da-nang/b', 'https://lozi.vn/a/da-nang/photos/do-an-ship', 'https://lozi.vn/a/da-nang/photos/goc-con-gai', 'https://lozi.vn/a/da-nang/photos/do-con-trai', 'https://lozi.vn/a/da-nang/photos/my-pham', 'https://lozi.vn/a/da-nang/photos/do-dien-tu', 'https://lozi.vn/a/da-nang/photos/do-gia-dung', 'https://lozi.vn/a/da-nang/photos/me-va-be', 'https://lozi.vn/a/da-nang/photos/fan-han-quoc', 'https://lozi.vn/a/da-nang/photos/fan-nhat-ban', 'https://lozi.vn/a/da-nang/photos/xe-co', 'https://lozi.vn/a/da-nang/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/da-nang/photos/sneaker', 'https://lozi.vn/a/da-nang/photos/toc-spa', 'https://lozi.vn/a/da-nang/photos/thu-cung', 'https://lozi.vn/a/da-nang/photos/sach-va-truyen', 'https://lozi.vn/a/da-nang/photos/do-choi-va-so-thich', 'https://lozi.vn/a/da-nang/photos/dung-cu-am-nhac', 'https://lozi.vn/a/da-nang/photos/vat-dung-trang-tri', 'https://lozi.vn/a/da-nang/photos/nha-phong-tro', 'https://lozi.vn/a/da-nang/photos/hang-order', 'https://lozi.vn/a/da-nang/photos/can-mua', 'https://lozi.vn/a/da-nang/photos/homestay', 'https://lozi.vn/a/da-nang/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/da-nang/photos/khac', 'https://lozi.vn/a/da-nang/photos/quan-tam', 'https://lozi.vn/a/ho-chi-minh/photos/do-an', 'https://lozi.vn/a/ho-chi-minh/b', 'https://lozi.vn/a/ho-chi-minh/photos/do-an-ship', 'https://lozi.vn/a/ho-chi-minh/photos/goc-con-gai', 'https://lozi.vn/a/ho-chi-minh/photos/do-con-trai', 'https://lozi.vn/a/ho-chi-minh/photos/my-pham', 'https://lozi.vn/a/ho-chi-minh/photos/do-dien-tu', 'https://lozi.vn/a/ho-chi-minh/photos/do-gia-dung', 'https://lozi.vn/a/ho-chi-minh/photos/me-va-be', 'https://lozi.vn/a/ho-chi-minh/photos/fan-han-quoc', 'https://lozi.vn/a/ho-chi-minh/photos/fan-nhat-ban', 'https://lozi.vn/a/ho-chi-minh/photos/xe-co', 'https://lozi.vn/a/ho-chi-minh/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/ho-chi-minh/photos/sneaker', 'https://lozi.vn/a/ho-chi-minh/photos/toc-spa', 'https://lozi.vn/a/ho-chi-minh/photos/thu-cung', 'https://lozi.vn/a/ho-chi-minh/photos/sach-va-truyen', 'https://lozi.vn/a/ho-chi-minh/photos/do-choi-va-so-thich', 'https://lozi.vn/a/ho-chi-minh/photos/dung-cu-am-nhac', 'https://lozi.vn/a/ho-chi-minh/photos/vat-dung-trang-tri', 'https://lozi.vn/a/ho-chi-minh/photos/nha-phong-tro', 'https://lozi.vn/a/ho-chi-minh/photos/hang-order', 'https://lozi.vn/a/ho-chi-minh/photos/can-mua', 'https://lozi.vn/a/ho-chi-minh/photos/homestay', 'https://lozi.vn/a/ho-chi-minh/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/ho-chi-minh/photos/khac', 'https://lozi.vn/a/ho-chi-minh/photos/quan-tam', 'https://lozi.vn/a/can-tho/photos/do-an', 'https://lozi.vn/a/can-tho/b', 'https://lozi.vn/a/can-tho/photos/do-an-ship', 'https://lozi.vn/a/can-tho/photos/goc-con-gai', 'https://lozi.vn/a/can-tho/photos/do-con-trai', 'https://lozi.vn/a/can-tho/photos/my-pham', 'https://lozi.vn/a/can-tho/photos/do-dien-tu', 'https://lozi.vn/a/can-tho/photos/do-gia-dung', 'https://lozi.vn/a/can-tho/photos/me-va-be', 'https://lozi.vn/a/can-tho/photos/fan-han-quoc', 'https://lozi.vn/a/can-tho/photos/fan-nhat-ban', 'https://lozi.vn/a/can-tho/photos/xe-co', 'https://lozi.vn/a/can-tho/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/can-tho/photos/sneaker', 'https://lozi.vn/a/can-tho/photos/toc-spa', 'https://lozi.vn/a/can-tho/photos/thu-cung', 'https://lozi.vn/a/can-tho/photos/sach-va-truyen', 'https://lozi.vn/a/can-tho/photos/do-choi-va-so-thich', 'https://lozi.vn/a/can-tho/photos/dung-cu-am-nhac', 'https://lozi.vn/a/can-tho/photos/vat-dung-trang-tri', 'https://lozi.vn/a/can-tho/photos/nha-phong-tro', 'https://lozi.vn/a/can-tho/photos/hang-order', 'https://lozi.vn/a/can-tho/photos/can-mua', 'https://lozi.vn/a/can-tho/photos/homestay', 'https://lozi.vn/a/can-tho/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/can-tho/photos/khac', 'https://lozi.vn/a/can-tho/photos/quan-tam', 'https://lozi.vn/a/nghe-an/photos/do-an', 'https://lozi.vn/a/nghe-an/b', 'https://lozi.vn/a/nghe-an/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/photos/my-pham', 'https://lozi.vn/a/nghe-an/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/photos/me-va-be', 'https://lozi.vn/a/nghe-an/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/photos/xe-co', 'https://lozi.vn/a/nghe-an/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/photos/sneaker', 'https://lozi.vn/a/nghe-an/photos/toc-spa', 'https://lozi.vn/a/nghe-an/photos/thu-cung', 'https://lozi.vn/a/nghe-an/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/photos/hang-order', 'https://lozi.vn/a/nghe-an/photos/can-mua', 'https://lozi.vn/a/nghe-an/photos/homestay', 'https://lozi.vn/a/nghe-an/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/photos/khac', 'https://lozi.vn/a/nghe-an/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-do-luong/b', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-do-luong/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/b', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-hung-nguyen/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-ky-son/b', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-ky-son/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/b', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-nam-dan/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/b', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-nghi-loc/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/b', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-nghia-dan/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-que-phong/b', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-que-phong/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/b', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-quy-chau/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/b', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-quy-hop/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/b', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-quynh-luu/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/b', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-tan-ky/photos/quan-tam', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-an', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/b', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/my-pham', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/me-va-be', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/xe-co', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/sneaker', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/toc-spa', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/thu-cung', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/hang-order', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/can-mua', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/homestay', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/khac', 'https://lozi.vn/a/nghe-an/thi-xa-thai-hoa/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/b', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-thanh-chuong/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/b', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-tuong-duong/photos/quan-tam', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-an', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/b', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/my-pham', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/me-va-be', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/xe-co', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/sneaker', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/toc-spa', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/thu-cung', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/hang-order', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/can-mua', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/homestay', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/khac', 'https://lozi.vn/a/nghe-an/thanh-pho-vinh/photos/quan-tam', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-an', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/b', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-an-ship', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/goc-con-gai', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-con-trai', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/my-pham', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-dien-tu', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-gia-dung', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/me-va-be', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/fan-han-quoc', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/fan-nhat-ban', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/xe-co', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/phu-kien-thoi-trang', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/sneaker', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/toc-spa', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/thu-cung', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/sach-va-truyen', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/do-choi-va-so-thich', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/dung-cu-am-nhac', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/vat-dung-trang-tri', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/nha-phong-tro', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/hang-order', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/can-mua', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/homestay', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/coupon-giam-gia-give-away', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/khac', 'https://lozi.vn/a/nghe-an/huyen-yen-thanh/photos/quan-tam']
    # urls = []
    # browser.get(BASE_URL)
    # m=0
    # wait.until(lambda browser: browser.find_element_by_css_selector('#app-view > div.nav-bar-wrapper > div > div > div.nb-left > a.btn-city'))
    # browser.find_element_by_css_selector('#app-view > div.nav-bar-wrapper > div > div > div.nb-left > a.btn-city').click()
    # wait.until(lambda browser: browser.find_element_by_css_selector('#app-view > div.popup-container > span:nth-child(23) > div > div > div.popup.popup-city > div.popup-body > ul'))
    # elements = browser.find_elements_by_css_selector('#app-view > div.popup-container > span:nth-child(23) > div > div > div.popup.popup-city > div.popup-body > ul > li')
    # while m < len(elements):
    #     if m!=0:
    #         wait.until(lambda browser: browser.find_element_by_css_selector('#app-view > div.nav-bar-wrapper > div > div > div.nb-left > a.btn-city'))
    #         browser.find_element_by_css_selector('#app-view > div.nav-bar-wrapper > div > div > div.nb-left > a.btn-city').click()
    #         wait.until(lambda browser: browser.find_element_by_css_selector('#app-view > div.popup-container > span:nth-child(23) > div > div > div.popup.popup-city > div.popup-body > ul'))
    #         elements = browser.find_elements_by_css_selector('#app-view > div.popup-container > span:nth-child(23) > div > div > div.popup.popup-city > div.popup-body > ul > li')
    #     browser.execute_script("arguments[0].scrollIntoView();", elements[m])
    #     time.sleep(2)
    #     k=0
    #     elements[m].click()
    #     elems = browser.find_elements_by_css_selector('#app-view > div.mode-bar > div > ul > li')
    #     for item in elems:
    #         time.sleep(2)
    #         try:
    #             href = item.find_element_by_css_selector('a').get_attribute("href")
    #             browser.get(href)
    #         except StaleElementReferenceException:
    #             continue
    #         try:
    #             elms = browser.find_elements_by_css_selector('a.btn-see-more-top-topic')
    #             for el in elms:
    #                 hre = el.get_attribute("href")
    #                 if hre not in urls:
    #                     urls.append(hre)
    #         except NoSuchElementException:
    #             k=1
    #         except StaleElementReferenceException:
    #             k=1
    #         # title = item.find_element_by_css_selector('span').text.strip()
    #         if k ==1:
    #             if href not in urls:
    #                 urls.append(href)
    #             # titles.append(title)
    #     m+=1
    # print(len(urls))
    # print(urls)
    # print(len(titles))
    # print(titles)
    j=0
    while j < len(urls):
        
        browser.get(urls[j])

        # try:
        #     elms = browser.find_elements_by_css_selector('a.btn-see-more-top-topic')
        # except NoSuchElementException:
        #     k=1
        # except StaleElementReferenceException:
        #     k=1


        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            # try:
            #     elem = browser.find_element_by_css_selector('#more')
            #     while elem.is_displayed():
            #         time.sleep(1.5)
            #         browser.execute_script("arguments[0].click();", elem)
            #         time.sleep(1.5)
            # except NoSuchElementException:
            #     k=1
            # except StaleElementReferenceException:
            #     k=1
            element = browser.find_element_by_xpath('/html/body')
            element.send_keys(Keys.END)
            element = browser.find_element_by_xpath('/html/body')
            element.send_keys(Keys.END)
            time.sleep(20)
            try:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='wrap-list-item').find_all('li')
            except:
                break
            b=0
            count = 10000
            while len(list) < count:
                old_list = len(list)
                time.sleep(2)
                element = browser.find_element_by_xpath('/html/body')
                element.send_keys(Keys.END)
                # browser.execute_script("window.scrollTo(0, document.body.scrollHeight*100);")
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='wrap-list-item').find_all('li')
                if old_list == len(list):
                    b+=1
                else:
                    b=0
                if b == 10:
                    break
            # print(len(list))
            # print(i+1)
            category = soup.find('h4', class_='cate-name').text.strip()
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            for item in list:
                # ---location 
                # ---address (field "Địa chỉ"),
                # ---price,
                # ---old_price (previous price if exists),
                # ---seller (account name prefix with '@', for example: "@vansympa")
                # ---category (name of category),
                # ---current date

                try:
                    location = soup.find('a', class_='btn-city').text.replace('tại','').strip()
                except:
                    location = None

                try:
                    address = item.find('span', class_='address-text').text.strip()
                except:
                    address = None

                try:
                    seller = item.find('span', class_='username').text.strip()
                except:
                    seller = None
                    continue

                try:
                    price = item.find('h3', class_='price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                except:
                    price = None
                # print("Price: " + str(price))
                try:
                    old_price = item.find('span', class_='trueprice').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                except:
                    old_price = None
                
                # ---location 
                # ---address (field "Địa chỉ"),
                # ---price,
                # ---old_price (previous price if exists),
                # ---seller (account name prefix with '@', for example: "@vansympa")
                # ---category (name of category),
                # ---current date
                data = {'category': category,
                        'location': location,
                        'seller': seller,
                        'address': address,
                        'price': price,
                        # 'old_price': old_price,
                        'date': DATE}
                write_csv(data)
            i+=1
        j+=1
    browser.quit()
    compress_data()

def compress_data():
    """Compress downloaded .csv and .html files"""
    os.chdir(PATH_CSV)
    z = zipfile.ZipFile(SITE_NAME + "_" + DATE + "_csv.zip", "a")
    z.write(SITE_NAME + "_" + DATE + ".csv")
    os.remove(SITE_NAME + "_" + DATE + ".csv")

    os.chdir(PATH_HTML)
    z = zipfile.ZipFile(SITE_NAME + "_" + DATE + "_html.zip", "a")
    for file in glob.glob("*.html"):
        z.write(file)
        os.remove(file)

if "test" in sys.argv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
