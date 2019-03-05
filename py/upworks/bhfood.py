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


SITE_NAME = "bhfood"
BASE_URL = "http://bhfood.vn"
PROJECT_PATH = os.getcwd()
PROJECT_PATH = PROJECT_PATH.replace("\\",'/')
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
            writer.writerow(('category', 'good_name', 'id', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['good_name'], data['id_'], data['price'], data['old_price'], data['date']))

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
    wait = ui.WebDriverWait(browser,5)
    urls = []
    titles = []
    browser.get(BASE_URL)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    write_html(browser.page_source, "All_cat_")
    menu_list = soup.find('ul', id='menu_categfory').find_all('a')
    for item in menu_list:
        href = item.get('href')
        title = item.text.strip()
        if href not in urls:
            urls.append(href)
            titles.append(title)
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        try:
            browser.get(urls[j])
        except TimeoutException:
            j+=1
            continue

        category = titles[j]


        # print(page_count)

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('ul.pagination'))
                    elements = browser.find_elements_by_css_selector('ul.pagination li')
                    if len(elements) == 1:
                        break
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
                    list = soup.find('div', id='content').find_all('div', class_='product-layout')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', id='content').find_all('div', class_='product-layout')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # ---good_name (name of product in Vietnamese),
                # ---price,
                # ---old_price (previous price if exists),
                # ---id (product_id by seller - could be created from the link),
                # ---category (name of category),
                # ---date (current date)


                try:
                    good_name = item.find('div', class_='caption').find('h4').text.strip()
                except:
                    good_name = None

                try:
                    id_ = item.find('div', class_='caption').find('h4').find('a').get('href')
                except:
                    id_ = None

                try:
                    price = item.find('span', class_='price-new').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                except:
                    try:
                        price_tax = item.find('span', class_='price-tax').text.strip()
                        price = item.find('p', class_='price').text.replace(price_tax,'').strip()
                    except:
                        price = None
                # print("Price: " + str(price))
                try:
                    old_price = item.find('span', class_='price-old').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                except:
                    old_price = None

                data = {'category': category,
                        'good_name': good_name,
                        'id_': id_,
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

# if __name__ == '__main__':
#     daily_task()
