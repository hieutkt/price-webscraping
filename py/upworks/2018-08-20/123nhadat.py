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
from selenium.webdriver.support.ui import Select



SITE_NAME = "123nhadat"
BASE_URL = "http://123nhadat.vn"
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
            writer.writerow(('category', 'location', 'floor_area', 'legal_right', 'description', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['location'], data['floor_area'], data['legal_right'], data['description'], data['price'],data['old_price'], data['date']))

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
    urls = ['http://123nhadat.vn/raovat-c1/nha-dat-ban', 'http://123nhadat.vn/raovat-c2/nha-dat-cho-thue']
    j=0
    while j < len(urls):
        browser.get(urls[j])

        soup = BeautifulSoup(browser.page_source, 'lxml')
        category = soup.find('div', class_='child_C').find('strong', class_='lamlam').text.strip()

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div:nth-child(4) > ul'))
                    elements = browser.find_elements_by_css_selector('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div:nth-child(4) > ul > li a')
                    c=0
                    while c < len(elements):
                        class_name = elements[c].get_attribute("class")
                        # try:
                        #     class_name = elements[c].find_element_by_css_selector('a').get_attribute("class")
                        # except NoSuchElementException:
                        #     c+=1
                        #     continue
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
                    list = soup.select('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div')[2]
                    list = list.find_all('div', class_='box_nhadatban')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.select('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div')[2]
                    list = list.find_all('div', class_='box_nhadatban')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a') == None:
                    continue
                else:
                    href = item.find('a').get('href')
                    try:
                        browser2.get(href)
                    except TimeoutException:
                        continue
                
                soup = BeautifulSoup(browser2.page_source, 'lxml')
                

                # ---111111111111111111111111111111price, (shown as "Giá”)
                # ---old_price (previous price if exists), 
                # ---1111111111111111111111111111location, (shown as "Địa chỉ của bất động sản")
                # ---1111111111111111111111111111floor area, (shown as "Diện tích")
                # ---1111111111111111111111111111legal right, (shown as "Pháp lý")
                # ---1111111111111111111111111111description, (text under “THÔNG TIN MÔ TẢ” section)
                # ---11111111111111111111111111111name of category,
                # ---11111111111111111111111111111current date

                try:
                    price = soup.find('ul', class_='info_no1').find('b', class_='camcam').text.strip()
                except:
                    price = None

                try:
                    li = soup.select('ul.info_no1 > li')[1]
                    floor_area = li.find('b', class_='camcam').text.strip()
                except:
                    floor_area = None

                try:
                    # p = soup.select('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div')[15]
                    # p = p.find('div', class_='detail_khungxam').find('p')
                    p = browser2.find_element_by_css_selector('div.content_C > div:nth-child(16) > div.detail_khungxam > p').text.strip()
                    description = p
                except NoSuchElementException:
                    description = None
                except:
                    description = None

                try:
                    # p = soup.select('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div')[16]
                    # p = soup.select('div.detail_khungxam > div')[1]
                    p = browser2.find_element_by_css_selector('div.content_C > div:nth-child(17) > div.detail_khungxam > div:nth-child(2)').text.strip()
                    location = p
                    location = location.replace('Địa chỉ của bất động sản', '').strip()
                    location = location.replace(':', '').strip()
                except NoSuchElementException:
                    location = None
                except:
                    location = None

                legal_right = None
                try:
                    lis = soup.find('ul', class_='thongsonha').find_all('li')
                    for li in lis:
                        txt = li.text.strip()
                        if "Pháp lý:" in txt:
                            legal_right = txt.replace('Pháp lý:', '').strip()
                except:
                    legal_right = None

                if soup.find('span', class_='price-old') != None:
                    old_price = soup.find('span', class_='price-old').text.strip()
                else:
                    old_price = None


                data = {'category': category,
                        'location': location,
                        'floor_area': floor_area,
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
    browser.quit()
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
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
