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


SITE_NAME = "muamuaonline"
BASE_URL = "https://muamuaonline.com"
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
            writer.writerow(('category', 'name', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['name'], data['brand'], data['price'], data['old_price'], data['date']))

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
    titles = []
    browser.get(BASE_URL)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    write_html(browser.page_source, "All_cat_")
    menu_list = soup.find('ul', class_='menu_left').find_all('ul', class_='sub_menu')
    for item in menu_list:
        menu_list2 = item.find_all('a', class_='sub_menuTitle')
        for item2 in menu_list2:
            href = BASE_URL + item2.get('href')
            title = item2.text.strip()
            if href not in urls:
                urls.append(href)
                titles.append(title)
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):

        browser.get(urls[j])

        category = titles[j]


        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            try:
                elem = browser.find_element_by_css_selector('#more')
                while elem.is_displayed():
                    time.sleep(1.5)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1.5)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('ul', id='loading-item').find_all('li')
            # print(len(list))
            # print(i+1)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            for item in list:
                # ---name,
                # ---price,
                # ---brand (field "Thương hiệu")
                # ---old_price (previous price if exists),
                # ---category (name of category),
                # ---current date

                try:
                    href = BASE_URL + item.find('div', class_='info_deal').find('a').get('href')
                    browser.get(href)
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    brand = soup.find('div', class_='detail_bar').find('a').text.strip()
                except:
                    brand = None

                try:
                    name = item.find('h4', class_='list_name').text.strip()
                except:
                    name = None

                try:
                    price = item.find('span', class_='price').text.strip()
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


                data = {'category': category,
                        'name': name,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': DATE}
                write_csv(data)
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
