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
import random
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
import signal


SITE_NAME = "hasaki"
BASE_URL = "https://hasaki.vn"
PROJECT_PATH = re.sub("/py/.+", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CHROME_DRIVER_PATH = PROJECT_PATH + "/bin/chromedriver"

def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'vietnam_name', 'english_name', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['vietnam_name'], data['english_name'], data['brand'], data['price'], data['old_price'], data['date']))

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
    browser = webdriver.Chrome(options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(options=chromeOptions)
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,30)
    urls = []
    urls = ['https://hasaki.vn/suc-khoe-lam-dep.html', 'https://hasaki.vn/suc-khoe-lam-dep/trang-diem.html', 'https://hasaki.vn/suc-khoe-lam-dep/cham-soc-da-mat.html', 'https://hasaki.vn/suc-khoe-lam-dep/cham-soc-co-the.html', 'https://hasaki.vn/suc-khoe-lam-dep/cham-soc-toc.html', 'https://hasaki.vn/me-va-be.html', 'https://hasaki.vn/me-va-be/be-ve-sinh.html', 'https://hasaki.vn/me-va-be/be-an.html', 'https://hasaki.vn/spa.html', 'https://hasaki.vn/hasaki-spa/giam-beo.html', 'https://hasaki.vn/hasaki-spa/triet-long-vinh-vien.html']
    titles = []
    titles = ['Sức Khỏe Làm Đẹp', 'Trang Điểm', 'Chăm Sóc Da Mặt', 'Chăm Sóc Cơ Thể', 'Chăm Sóc Tóc', 'Ba Mẹ Và Bé - Đồ chơi', 'Bé Vệ Sinh', 'Bé Ăn', 'Hasaki Clinic & Spa', 'Giảm Béo', 'Triệt Lông']
    browser.get(BASE_URL)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    write_html(browser.page_source, "All_cat_")
    menu_list = soup.find('div', id='sub_menu_web').find_all('a', class_='parent_menu')
    for item in menu_list:
        href = BASE_URL + item.get('href')
        title = item.text.strip()
        if href not in urls:
            urls.append(href)
            titles.append(title)
        # browser.get(BASE_URL+item.get('href'))
        # soup = BeautifulSoup(browser.page_source, 'lxml')
        # try:
        #     menu_list2 = soup.find('div', class_='content_fillter').find_all('a', class_='item_fillter')
        # except:
        #     continue
        # for item2 in menu_list2:
        #     href = item2.get('href')
        #     title = item2.text.strip()
        #     if href not in urls:
        #         urls.append(href)
        #         titles.append(title)
    # print(len(titles))
    # print(titles)
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])

        category = titles[j]


        # print(page_count)

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#col_right > nav > ul'))
                    elements = browser.find_elements_by_css_selector('#col_right > nav > ul > li')
                    c=0
                    while c < len(elements):
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-1 >= c+1:
                                href_glob = elements[c+1].find_element_by_css_selector('a').get_attribute("href")
                                browser.get(href_glob)
                                c+=1
                                break
                            else:
                                pagination = False
                                c+=1
                                break
                        c+=1
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='list_product').find_all('div', class_='product_item')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='list_product').find_all('div', class_='product_item')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # ---name,
                # ---price,
                # ---brand
                # ---old_price (previous price if exists),
                # ---category (name of category),
                # ---current date

                try:
                    brand = item.find('div', class_='product_shopping').text.strip()
                except:
                    brand = None

                try:
                    vietnam_name = item.find('div', class_='vietnam_name').text.strip()
                except:
                    vietnam_name = None

                try:
                    english_name = item.find('div', class_='english_name').text.strip()
                except:
                    english_name = None

                try:
                    price = item.find('span', class_='giamoi').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                except:
                    price = None

                try:
                    old_price = item.find('span', class_='giacu').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                except:
                    old_price = None


                data = {'category': category,
                        'vietnam_name': vietnam_name,
                        'english_name': english_name,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': DATE}
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
