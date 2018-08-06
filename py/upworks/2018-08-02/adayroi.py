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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException


SITE_NAME = "adayroi"
BASE_URL = "https://www.adayroi.com"
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
            writer.writerow(('category', 'id', 'good_name', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['good_name'], data['price'], data['old_price'], data['date']))

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
    # chromeOptions.add_argument("--disable-javascript")
    chromeOptions.add_argument("--headless")
    # PROXY = "212.34.52.43:8080" # IP:PORT or HOST:PORT
    # chromeOptions.add_argument('--proxy-server=http://%s' % PROXY)
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,5)
    browser.get(BASE_URL)
    urls = []
    titles = []
    soup = BeautifulSoup(browser.page_source, 'lxml')
    category_list = soup.find('ul', class_='menu__cat-list').find_all('li', class_='menu__cat-item')
    c=0
    for item in category_list:
        if c < 2:
            c+=1
            continue
        url_list = item.find('div', class_='menu__cat-list').find_all('a', class_='item-strong')
        url = url_list[len(url_list)-1]
        url = BASE_URL + url.get('href')
        title = item.find('a', class_='menu__cat-link').text.strip()
        urls.append(url)
        titles.append(title)
        c+=1
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        browser.get(urls[j])

        category = titles[j]

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait2.until(lambda browser: browser.find_element_by_css_selector('#content > div > div.category__section.category__section-5 > div > div > div.col-sm-12.col-md-9.col-lg-10.product-list__wrapper > section > nav > ul'))
                    elements = browser.find_elements_by_css_selector('#content > div > div.category__section.category__section-5 > div > div > div.col-sm-12.col-md-9.col-lg-10.product-list__wrapper > section > nav > ul > li')
                    c=0
                    while c < len(elements)-1:
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-2 >= c+1:
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
                    elements = browser.find_elements_by_css_selector('div.product-list__container > div > div')
                except:
                    pagination = False
            if i == 0:
                try:
                    elements = browser.find_elements_by_css_selector('div.product-list__container > div > div')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for element in elements:
                item = element.get_attribute('innerHTML')
                item = BeautifulSoup(item, 'lxml')
                # print(item)
                if item.find('a') != None:
                    id_ = BASE_URL + item.find('a').get('href')
                    # id_ = id_.split('offer=')[1]
                    # id_ = id_.split('_')
                    # if len(id_) == 2:
                    #     id_ = id_[0]
                    #     id_ = id_.strip()
                    # elif len(id_) == 3:
                    #     id_ = id_[1]
                    #     id_ = id_.strip()
                    # else:
                    #     id_ = BASE_URL + item.find('a').get('href')
                else:
                    id_ = None

                # if item.find('a') != None:
                #     brand = item.find('a').get('href')
                # else:
                #     brand = None

                # if item.find('span', class_='dst_primtitle') != None:
                #     good_name_english = item.find('span', class_='dst_primtitle').text.strip()
                # else:
                #     good_name_english = None

                if item.find('h3', class_='product-item__info-title') != None:
                    good_name = item.find('h3', class_='product-item__info-title').text.strip()
                elif item.find('a', class_='product-item__info-title') != None:
                    good_name = item.find('a', class_='product-item__info-title').text.strip()
                else:
                    good_name = None

                if item.find('span', class_='product-item__info-price-sale') != None:
                    price = item.find('span', class_='product-item__info-price-sale').text.strip()
                else:
                    price = None

                if item.find('span', class_='product-item__info-price-original') != None:
                    old_price = item.find('span', class_='product-item__info-price-original').text.strip()
                else:
                    old_price = None
                
                data = {'category': category,
                        'id': id_,
                        # 'brand': brand,
                        # 'good_name_english': good_name_english,
                        'good_name': good_name,
                        'price': price,
                        'old_price': old_price,
                        'date': DATE}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
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
