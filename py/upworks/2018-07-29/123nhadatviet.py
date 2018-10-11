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


SITE_NAME = "123nhadatviet"
BASE_URL = "http://123nhadatviet.com"
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
            writer.writerow(('category', 'description', 'price', 'property_type', 'legal_right', 'floor_area', 'location', 'date'))
        writer.writerow((data['category'], data['description'], data['price'], data['property_type'], data['legal_right'], data['floor_area'], data['location'], data['date']))

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
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    urls = ['http://123nhadatviet.com/rao-vat/can-ban/nha-dat.html', 'http://123nhadatviet.com/rao-vat/cho-thue/nha-dat.html']
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])
        wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="left"]/div[2]'))
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category_titles = soup.find('div', class_='top-link').find_all('a')
        if len(category_titles) == 2:
            category = category_titles[1].find('span').text.strip()
        if len(category_titles) == 3:
            category = category_titles[1].find('span').text.strip()
        if len(category_titles) == 4:
            category = category_titles[1].find('span').text.strip()

        i=0
        pagination = True
        while pagination:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                if i == 1:
                    browser.get(urls[j])
                    file_name = str(j+1) + "_" + str(i) + "_"
                    write_html(browser.page_source, file_name)
                else:
                    browser.get(href_glob)
                    file_name = str(j+1) + "_" + str(i) + "_"
                    write_html(browser.page_source, file_name)
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="left"]/div[2]'))
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
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="left"]/div[2]'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='content-item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='content-item')
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # if item.find('div', class_='ct_title') != None:
                #     title = item.find('div', class_='ct_title').text.strip()
                # else:
                #     title = None
                href = BASE_URL + item.find('div', class_='ct_title').find('a').get('href')
                browser.get(href)
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="left"]/div[2]'))
                soup = BeautifulSoup(browser.page_source, 'lxml')

                try:
                    if soup.find('div', class_='address') != None:
                        location = soup.find('div', class_='address').find('span', class_='value').text.strip()
                        # location = location.replace('Địa chỉ:', '')
                        # location = location.strip()
                    else:
                        location = None
                except:
                    location = None

                try:
                    trs = soup.find('div', class_='infor').find('tbody').find_all('tr')
                    tds = trs[3].find_all('td')
                    property_type = tds[1].text.strip()
                    tds = trs[6].find_all('td')
                    floor_area = tds[1].text.strip()
                    tds = trs[3].find_all('td')
                    legal_right = tds[3].text.strip()
                except:
                    property_type = None
                    floor_area = None
                    legal_right = None

                # ---floor area, (shown as "Diện tích")
                # ---property type, (shown as "Loại BDS")
                # ---legal right, (shown as "Pháp lý")
                # ---description, (shown as "Thông tin mô tả")

                # if item.find('div', class_='ct_dt') != None:
                #     floor_area = item.find('div', class_='ct_dt').text.strip()
                # else:
                #     floor_area = None

                # if item.find('div', class_='ct_kt') != None:
                #     Dimensions = item.find('div', class_='ct_kt').text.strip()
                # else:
                #     Dimensions = None

                # if item.find('div', class_='english_name') != None:
                #     property_type = item.find('div', class_='english_name').text.strip()
                # else:
                #     property_type = None

                if soup.find('div', class_='detail') != None:
                    description = soup.find('div', class_='detail').text.strip()
                else:
                    description = None

                # if item.find('div', class_='ct_direct') != None:
                #     Direction = item.find('div', class_='ct_direct').text.strip()
                # else:
                #     Direction = None
                # print("Title: " + title)
                if soup.find('td', class_='price') != None:
                    price = soup.find('td', class_='price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None

                # if item.find('div', class_='ct_date') != None:
                #     Posted = item.find('div', class_='ct_date').text.strip()
                # else:
                #     Posted = None
                
                data = {'category': category,
                        'description': description,
                        'price': price,
                        'property_type': property_type,
                        'legal_right': legal_right,
                        'floor_area': floor_area,
                        'location': location,
                        'date': DATE}
                write_csv(data)
            # file_name = str(j+1) + "_" + str(i+1) + "_"
            # write_html(browser.page_source, file_name)
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
