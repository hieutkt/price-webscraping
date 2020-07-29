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


SITE_NAME = "lotte"
BASE_URL = "https://www.lotte.vn"
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
            writer.writerow(('category', 'id', 'title', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['title'], data['brand'], data['price'], data['old_price'], data['date']))

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
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,30)
    urls = []
    # try:
    browser.get(BASE_URL)
    wait.until(lambda browser: browser.find_elements_by_css_selector('div.menu-row ul.menu-items'))
    soup = BeautifulSoup(browser.page_source, 'lxml')
    write_html(browser.page_source, "All_cat_")
    menu_list = soup.find('div', class_='menu-row').find_all('ul', class_='menu-items')
    for item in menu_list:
        menu_list2 = item.find_all('li')
        for item2 in menu_list2:
            if "/category/" in item2.find('a').get('href'):
                href = BASE_URL + item2.find('a').get('href')
            else:
                href = BASE_URL + '/' + item2.find('a').get('href')
            try:
                browser.get(href)
                wait.until(lambda browser: browser.find_element_by_css_selector('#maincontent > app-category-fs > app-common-fs-category-tree > section > div > div > ul'))
            except TimeoutException:
                continue
            soup = BeautifulSoup(browser.page_source, 'lxml')
            menu_list3 = soup.find('section', class_='cate-filter-menu').find('ul').find_all('li')
            for item3 in menu_list3:
                if "/category/" in item3.find('a').get('href'):
                    href = BASE_URL + item3.find('a').get('href')
                else:
                    href = BASE_URL + '/' + item3.find('a').get('href')
                try:
                    browser.get(href)
                    wait.until(lambda browser: browser.find_element_by_css_selector('#maincontent > app-category-fs > app-common-fs-category-tree > section > div > div > ul'))
                except TimeoutException:
                    if href not in urls:
                        urls.append(href)
                    continue
                soup = BeautifulSoup(browser.page_source, 'lxml')
                menu_list4 = soup.find('section', class_='cate-filter-menu').find('ul').find_all('li')
                for item4 in menu_list4:
                    if "/category/" in item4.find('a').get('href'):
                        href = BASE_URL + item4.find('a').get('href')
                    else:
                        href = BASE_URL + '/' + item4.find('a').get('href')
                    if href not in urls:
                        urls.append(href)
    # except TimeoutException:
    #     urls = []
    # except:
    #     urls = []
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        try:
            browser.get(urls[j])
            wait.until(lambda browser: browser.find_element_by_css_selector('#maincontent > app-category-fs > section > div > h1'))
            category = browser.find_element_by_css_selector('#maincontent > app-category-fs > section > div > h1').text.strip()
        except TimeoutException:
            j+=1
            continue

        try:
            wait.until(lambda browser: browser.find_elements_by_css_selector('#maincontent > app-category-fs > app-common-fs-products > main > div > app-common-fs-product-list > div > div'))
        except TimeoutException:
            j+=1
            continue


        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            try:
                elem = browser.find_element_by_css_selector('#maincontent > app-category-fs > app-common-fs-products > main > div > div > a')
                while elem.is_displayed():
                    time.sleep(1.5)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1.5)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', class_='products-cate-list').find_all('div', class_='item-product')
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a') == None:
                    continue
                # item_id = BASE_URL + item.find('a').get('href').strip()

                if "/product/" in item.find('a').get('href'):
                    item_id = BASE_URL + item.find('a').get('href').strip()
                else:
                    item_id = BASE_URL + '/' + item.find('a').get('href').strip()

                # ---price,
                # ---old_price (previous price if exists),
                # ---good_name_english (name of product in English - if available),
                # ---good_name (name of product in Vietnamese),
                # ---11111111111111111id (product_id by seller - could be created from the link),
                # ---11111111111111111category (name of category),
                # ---brand (if available),
                # ---111111111111111111date (current date),
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('span', class_='brand-name') != None:
                    brand = item.find('span', class_='brand-name').text.strip()
                else:
                    brand = None

                if item.find('div', class_='field-name') != None:
                    title = item.find('div', class_='field-name').text.strip()
                else:
                    title = None
                # if item.find('div', class_='english_name') != None:
                #     title_Vietnamese = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_Vietnamese = None
                # print("Title: " + title)
                if item.find('span', class_='current-price') != None:
                    price = item.find('span', class_='current-price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='old-price') != None:
                    old_price = item.find('span', class_='old-price').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None


                data = {'category': category,
                        'id': item_id,
                        'title': title,
                        'brand': brand,
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
# if __name__ == '__main__':
#     daily_task()
