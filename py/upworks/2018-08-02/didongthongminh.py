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
from selenium.common.exceptions import StaleElementReferenceException


SITE_NAME = "didongthongminh"
BASE_URL = "https://didongthongminh.vn"
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
            writer.writerow(('category', 'id', 'good_name', 'description', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['good_name'], data['description'], data['price'], data['old_price'], data['date']))

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
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,5)
    urls = ['https://didongthongminh.vn/dien-thoai', 'https://didongthongminh.vn/may-tinh-bang', 'https://didongthongminh.vn/phu-kien']
    j=0
    while j < len(urls):
        browser.get(urls[j])
        wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="main"]/header/h1'))
        soup = BeautifulSoup(browser.page_source, 'lxml')
        category = soup.find('h1', class_='woocommerce-products-header__title').text.strip()

        i=0
        pagination = True
        while pagination:
            try:
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-load-more-1"]/a'))
                element = browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-load-more-1"]/a')
                txt = browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-load-more-1"]/a').text.strip()
                while element.is_displayed():
                    browser.execute_script("arguments[0].click();", element)
                    try:
                        span = browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-loader-1"]/span').text.strip()
                        while "Đang tải..." in span:
                            time.sleep(1)
                            span = browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-loader-1"]/span').text.strip()
                    except StaleElementReferenceException:
                        c = 0
                    except NoSuchElementException:
                        c = 0
                    wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-load-more-1"]/a'))
                    txt = browser.find_element_by_xpath('//*[@id="sb-infinite-scroll-load-more-1"]/a').text.strip()
                    if "Đã tải xong..." in txt:
                        break
                pagination = False
                elements = browser.find_elements_by_css_selector('#main > ul.products > li')
            except NoSuchElementException:
                pagination = False
            except TimeoutException:
                pagination = False
            except:
                pagination = False
            # print(len(list))
            # print(i+1)
            for element in elements:
                item = element.get_attribute('innerHTML')
                item = BeautifulSoup(item, 'lxml')
                # print(item)
                if item.find('a') != None:
                    id_ = item.find('a').get('href')
                else:
                    id_ = None

                if item.find('span', class_='dst_primtitle') != None:
                    good_name = item.find('span', class_='dst_primtitle').text.strip()
                else:
                    good_name = None

                if item.find('span', class_='dst_subtitle') != None:
                    description = item.find('span', class_='dst_subtitle').text.strip()
                else:
                    description = None

                if item.find('span', class_='woocommerce-Price-amount') != None:
                    price = item.find('span', class_='woocommerce-Price-amount').text.strip()
                else:
                    price = None

                if item.find('span', class_='woocommerce-OldPrice-amount') != None:
                    old_price = item.find('span', class_='woocommerce-OldPrice-amount').text.strip()
                else:
                    old_price = None
                
                data = {'category': category,
                        'id': id_,
                        'good_name': good_name,
                        'description': description,
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
