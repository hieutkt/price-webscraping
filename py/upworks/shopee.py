from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
import random
import zipfile
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
import signal


SITE_NAME = "shopee"
BASE_URL = "https://shopee.vn"
PROJECT_PATH = re.sub("/py/upworks$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
# OPTIONS.add_argument("--headless")
OPTIONS.add_argument("start-maximized")
OPTIONS.add_argument("disable-infobars")
OPTIONS.add_argument("--disable-extensions")
OPTIONS.add_argument("--no-sandbox")
OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38



def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    fieldnames = ['category', 'sub_category', 'id', 'good_name',
                  'brand', 'price', 'old_price', 'date']
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter=',')
        writer.writerow(data)

def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    browser = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               options=OPTIONS)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    browser.get(BASE_URL)
    wait = ui.WebDriverWait(browser,60)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    urls = []
    try:
        category_list = soup.find('div', class_='section-category-list').find('ul', class_='image-carousel__item-list').find_all('a', class_='home-category-list__category-grid')
    except AttributeError:
        browser.find_element_by_tag_name('body').click()
        category_list = soup.find('div', class_='section-category-list').find('ul', class_='image-carousel__item-list').find_all('a', class_='home-category-list__category-grid')
    while len(category_list) < 20:
        time.sleep(1)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        category_list = soup.find('div', class_='section-category-list').find('ul', class_='image-carousel__item-list').find_all('a', class_='home-category-list__category-grid')
    for item in category_list:
        href = BASE_URL + item.get('href')
        urls.append(href)
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        browser.get(urls[j] + "?page=0&sortBy=pop")
        time.sleep(1)
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category = soup.find('div', class_='shopee-category-list__main-category--active').find('a').text.strip()


        i=0
        page_count = soup.find('span', class_='shopee-mini-page-controller__total').text.strip()
        while i < int(page_count):
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                browser.get(urls[j] + "?page=" + str(i) + "&sortBy=pop")
                time.sleep(1)
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='shopee-search-item-result__item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='shopee-search-item-result__item')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.find('a', class_='shopee-item-card--link')
                if item_id is not None:
                    item_id = item_id.get('href').strip()
                    # https://shopee.vn/%C3%81o-thun-nam-tay-d%C3%A0i-Amour-i.45223201.718824272
                    item_id = item_id.split('-i.')
                    item_id = item_id[len(item_id)-1]
                    item_id = item_id.strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                # if item.find('div', class_='name-brand') != None:
                #     brand = item.find('div', class_='name-brand').text.strip()
                # else:
                #     brand = None
                if item.find('div', class_='shopee-item-card__text-name') != None:
                    title_Vietnamese = item.find('div', class_='shopee-item-card__text-name').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('div', class_='shopee-item-card__current-price') != None:
                    price = item.find('div', class_='shopee-item-card__current-price').text.strip()
                    price = price.split('₫')[1]
                    price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('div', class_='shopee-item-card__original-price') != None:
                    old_price = item.find('div', class_='shopee-item-card__original-price').text.strip()
                    old_price = old_price.split('₫')[1]
                    old_price = old_price.strip()
                else:
                    old_price = None

                date = DATE

                data = {'category': category,
                        'id': item_id,
                        'good_name': title_Vietnamese,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            i+=1
        j+=1
    # Close browser
    browser.close()
    browser.service.process.send_signal(signal.SIGTERM)
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)
