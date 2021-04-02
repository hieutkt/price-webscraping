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


SITE_NAME = "dinhgianhadat"
BASE_URL = "https://dinhgianhadat.vn"
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
    chromeOptions.add_experimental_option("prefs",prefs)
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument("disable-infobars")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    browser2 = webdriver.Chrome(options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser = webdriver.Chrome(options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(options=chromeOptions)
    # browser = webdriver.Chrome(options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    urls = ['https://dinhgianhadat.vn/nha-dat-ban', 'https://dinhgianhadat.vn/nha-dat-cho-thue']
    j=0
    while j < len(urls):
        sys.stdout.write('Scraping ' + urls[j] + ' ...' + ' '*10)
        browser.get(urls[j])

        soup = BeautifulSoup(browser.page_source, 'lxml')
        category = soup.find('div', class_='title-group').find('h1').text.strip()

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#content > div.mt15.mb25.container > div > div > div.col-lg-9.col-md-9.col-sm-7.col-xs-12 > div.wrap-paging > div > nav > ul'))
                    elements = browser.find_elements_by_css_selector('#content > div.mt15.mb25.container > div > div > div.col-lg-9.col-md-9.col-sm-7.col-xs-12 > div.wrap-paging > div > nav > ul > li')
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
                    list = soup.find('ul', class_='list-product').find_all('li', class_='col-lg-6')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('ul', class_='list-product').find_all('li', class_='col-lg-6')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a', class_='link-title') == None:
                    continue
                else:
                    href = BASE_URL + item.find('a', class_='link-title').get('href')
                    try:
                        browser2.get(href)
                    except TimeoutException:
                        continue

                soup = BeautifulSoup(browser2.page_source, 'lxml')


                # ---11111111111111111111111111111111price, (shown as "Giá bán" or “Giá thuê”)
                # ---old_price (previous price if exists),
                # ---1111111111111111111111111111111location, (shown as " Vị trí")
                # ---11111111111111111111111111111111floor area, (shown as " DT khuôn viên")
                # ---legal right, (shown as "Giấy tờ pháp lý")
                # ---description, (text after "Giấy tờ pháp lý" line and before price line)
                # ---name of category,
                # ---111111111111111111111111111111111current date

                try:
                    price = soup.find('div', class_='wrap-price').find('div', class_='sell').text.strip()
                    price = price.replace('Giá thuê:', '').strip()
                except:
                    price = None

                try:
                    # li = soup.select('ul.info_no1 > li')[1]
                    floor_area = soup.find('li', class_='area').find('p').text.strip()
                except:
                    floor_area = None

                try:
                    location = soup.find('li', class_='localtion').find('p').text.strip()
                    location = location.replace('"','').strip()
                except:
                    location = None

                try:
                    # p = soup.select('body > div.jPanelMenu-panel > div.mainpage > div.content > div.content_C > div')[15]
                    description = soup.find('div', class_='col-info-product').find('div', class_='deatail').text.strip()
                    # p = browser2.find_element_by_css_selector('div.content_C > div:nth-child(16) > div.detail_khungxam > p').text.strip()
                    # description = p
                except:
                    description = None

                legal_right = None
                try:
                    lis = soup.find('div', class_='col-info-product').find_all('li', class_='direction')
                    for li in lis:
                        txt = li.text.strip()
                        if "Giấy tờ pháp lý" in txt:
                            legal_right = txt.replace('Giấy tờ pháp lý', '').strip()
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
