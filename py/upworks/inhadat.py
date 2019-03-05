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


SITE_NAME = "inhadat"
BASE_URL = "http://i-nhadat.com"
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
            writer.writerow(('category', 'location', 'floor_area', 'property_type', 'legal_right', 'description', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['location'], data['floor_area'], data['property_type'], data['legal_right'], data['description'], data['price'],data['old_price'], data['date']))

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
    browser2 = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    urls = ['http://i-nhadat.com/can-ban-nha-dat.htm', 'http://i-nhadat.com/cho-thue-nha-dat.htm']
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])

        wait.until(lambda browser: browser.find_element_by_css_selector('#wrapper > div.body > div.top-link > span:nth-child(2) > a > span'))
        category = browser.find_element_by_css_selector('#wrapper > div.body > div.top-link > span:nth-child(2) > a > span').text.strip()

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#left > div.page'))
                    elements = browser.find_elements_by_css_selector('#left > div.page > a')
                    c=0
                    while c < len(elements):
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-1 >= c+1:
                                href_glob = elements[c+1].get_attribute("href")
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
                    list = soup.find('div', class_='content-items').find_all('div', class_='content-item')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='content-items').find_all('div', class_='content-item')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('div', class_='ct_title').find('a') == None:
                    continue
                else:
                    href = BASE_URL + item.find('div', class_='ct_title').find('a').get('href')
                    try:
                        browser2.get(href)
                    except TimeoutException:
                        continue

                soup = BeautifulSoup(browser2.page_source, 'lxml')


                # ---1111111111111111111111111111111111price, (shown as "Giá”)
                # ---old_price (previous price if exists),
                # ---1111111111111111111111111111111111location, (shown as "Địa chỉ tài sản")
                # ---property type, (shown as “Loại BDS”)
                # • ---floor area, (shown as "Diện tích")
                # ---legal right, (shown as "Pháp lý")
                # ---1111111111111111111111111111111111description, (text under “Thông tin mô tả” section)
                # ---1111111111111111111111111111111111name of category,
                # ---1111111111111111111111111111111111current date

                try:
                    price = soup.find('td', class_='price').text.strip()
                except:
                    price = None


                try:
                    description = soup.find('div', id='left').find('div', class_='detail').text.strip()
                except NoSuchElementException:
                    description = None
                except:
                    description = None

                try:
                    location = soup.find('div', class_='address').find('span', class_='value').text.strip()
                except NoSuchElementException:
                    location = None
                except:
                    location = None

                legal_right = None
                property_type = None
                floor_area = None
                try:
                    trs = soup.find('div', class_='infor').find('tbody').find_all('tr')
                    for tr in trs:
                        tds = tr.find_all('td')
                        txt = tr.text.strip()
                        if "Pháp lý" in txt:
                            legal_right = tds[1].text.strip()
                        if "Loại BDS" in txt:
                            property_type = tds[3].text.strip()
                        if "Diện tích" in txt:
                            floor_area = tds[1].text.strip()
                except:
                    c = 0

                if soup.find('span', class_='price-old') != None:
                    old_price = soup.find('span', class_='price-old').text.strip()
                else:
                    old_price = None


                data = {'category': category,
                        'location': location,
                        'floor_area': floor_area,
                        'property_type': property_type,
                        'legal_right': legal_right,
                        'description': description,
                        'price': price,
                        'old_price': old_price,
                        'date': DATE}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            i+=1
        # print(j)
        j+=1
    # Close browser
    browser.close()
    browser.service.process.send_signal(signal.SIGTERM)
    browser.quit()
    # Close browser
    browser2.close()
    browser2.service.process.send_signal(signal.SIGTERM)
    browser2.quit()
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
