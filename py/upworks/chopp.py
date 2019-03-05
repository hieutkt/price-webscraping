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
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
# from selenium.webdriver.support import expected_conditions as EC
import zipfile
from selenium.webdriver.chrome.options import Options
import signal


SITE_NAME = "chopp"
BASE_URL = "https://chopp.vn"
PROJECT_PATH = re.sub("/py/upworks$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument("--headless")
OPTIONS.add_argument("start-maximized")
OPTIONS.add_argument("disable-infobars")
OPTIONS.add_argument("--disable-extensions")
OPTIONS.add_argument("--no-sandbox")
OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38
# prefs = {"profile.managed_default_content_settings.images":2}
# OPTIONS.add_experimental_option("prefs",prefs)


def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'seller', 'id', 'good_name', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['seller'], data['id'], data['good_name'], data['price'],data['old_price'], data['date']))


def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    browser = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    browser.get('https://chopp.vn/categories')
    wait = ui.WebDriverWait(browser,60)
    write_html(browser.page_source, "All_cat_")
    urls = []
    main_category_list = []
    wait.until(lambda browser: browser.find_elements_by_css_selector("div._19wIZMFilHrnKByimhQt7v > div.lz4VeJKCnYSlLdTZ0jG36"))
    soup = BeautifulSoup(browser.page_source, 'lxml')
    main_category_list_temp = soup.find('div', class_='_19wIZMFilHrnKByimhQt7v').find_all('div', class_='lz4VeJKCnYSlLdTZ0jG36')
    main_category_list.append(main_category_list_temp)
    k=0
    while k < 2:
        elements_category_old = browser.find_elements_by_css_selector("div._19wIZMFilHrnKByimhQt7v > div.lz4VeJKCnYSlLdTZ0jG36")
        wait.until(lambda browser: browser.find_elements_by_css_selector("div._3WOMXD7P4sk6Bbwbxybeqe > span.W_vStYGLcIkgiP1IjG5J0"))
        elements = browser.find_elements_by_css_selector("div._3WOMXD7P4sk6Bbwbxybeqe > span.W_vStYGLcIkgiP1IjG5J0")
        # browser.execute_script("arguments[0].click();", elements[k+1])
        elements[k+1].click()
        elements_category_new = browser.find_elements_by_css_selector("div._19wIZMFilHrnKByimhQt7v > div.lz4VeJKCnYSlLdTZ0jG36")
        while len(elements_category_old) == len(elements_category_new):
            time.sleep(1)
            elements[k+1].click()
            # browser.execute_script("arguments[0].click();", elements[k+1])
            elements_category_new = browser.find_elements_by_css_selector("div._19wIZMFilHrnKByimhQt7v > div.lz4VeJKCnYSlLdTZ0jG36")
        soup = BeautifulSoup(browser.page_source, 'lxml')
        main_category_list_temp = soup.find('div', class_='_19wIZMFilHrnKByimhQt7v').find_all('div', class_='lz4VeJKCnYSlLdTZ0jG36')
        main_category_list.append(main_category_list_temp)
        k+=1
    # print(len(main_category_list))
    # print(main_category_list)
    for main_item in main_category_list:
        for item in main_item:
            href = BASE_URL + item.find('a').get('href')
            browser.get(href)
        # _3XMKb7UizdtpkmzDv4Eqel
            try:
                wait.until(lambda browser: browser.find_element_by_css_selector("div._2w1tNoBizkR-Jrpj8JNOc1"))
                elem = browser.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div[2]/div[2]/button')
                while elem.is_displayed():
                    time.sleep(1)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            category_list = soup.find_all('div', class_='_2w1tNoBizkR-Jrpj8JNOc1')
            for item in category_list:
                url = BASE_URL + item.find('a').get('href')
                if url not in urls:
                    urls.append(url)
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        browser.get(urls[j])
        try:
            wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/h4'))
        except TimeoutException:
            j+=1
            continue
        soup = BeautifulSoup(browser.page_source, 'lxml')
        seller = soup.find('span', class_='_2S39cc96K0t16Uhtllv-CO').text.strip()
        category = soup.find('h4', class_='_1D3-Pi2MFSGjD8bd09uC-u').text.strip()
        category = category.replace(seller, '').strip()

        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            wait.until(lambda browser: browser.find_elements_by_css_selector("div._1vQvQQy_nRDaUE9bFMRd3b > div._1_EzvXCRpzUaMO5f5bX-g7"))
            try:
                elem = browser.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div[2]/button')
                while elem.is_displayed():
                    time.sleep(1)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', class_='_1vQvQQy_nRDaUE9bFMRd3b').find_all('div', class_='_1_EzvXCRpzUaMO5f5bX-g7')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = BASE_URL + item.find('a').get('href').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                # if item.find('div', class_='name-brand') != None:
                #     brand = item.find('div', class_='name-brand').text.strip()
                # else:
                #     brand = None
                if item.find('h5', class_='_2adSc_jj3OEkhxhIo8wIMi') != None:
                    title_English = item.find('h5', class_='_2adSc_jj3OEkhxhIo8wIMi').text.strip()
                else:
                    title_English = None
                # if item.find('div', class_='english_name') != None:
                #     title_Vietnamese = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_Vietnamese = None
                # print("Title: " + title)
                if item.find('span', class_='_21BTghMT3H9TvI52BA1Noz') != None:
                    price = item.find('span', class_='_21BTghMT3H9TvI52BA1Noz').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='o19Nz8WBfb8EWgMVut3Dc') != None:
                    old_price = item.find('span', class_='o19Nz8WBfb8EWgMVut3Dc').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None



                data = {'category': category,
                        'seller': seller,
                        'id': item_id,
                        'good_name': title_English,
                        # 'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': DATE}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
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
