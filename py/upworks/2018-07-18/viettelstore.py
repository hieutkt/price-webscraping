from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
from selenium.common.exceptions import NoSuchElementException
import selenium.webdriver.support.ui as ui
import zipfile
from selenium.webdriver.chrome.options import Options


SITE_NAME = "viettelstore"
BASE_URL = "https://viettelstore.vn"
PROJECT_PATH = re.sub("/py/upworks$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'id', 'good_name', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['good_name'], data['price'],data['old_price'], data['date']))


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
    browser.get(BASE_URL)
    wait = ui.WebDriverWait(browser,60)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    urls = []
    main_category_list = soup.select('div.owl-wrapper > div.owl-item')
    main_category_list = main_category_list[0:4]
    write_html(browser.page_source, "All_cat_")
    k=0
    sub_title = []
    for main_item in main_category_list:
        if k < 3:
            url = BASE_URL + main_item.find('a').get('href')
            urls.append(url)
        else:
            url = BASE_URL + main_item.find('a').get('href')
            browser.get(url)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            category_list = soup.find('div', id='owl-list-pk').find_all('div', class_='owl-item')
            for item in category_list:
                url = BASE_URL + item.find('div', class_='item-pk').find('a').get('href')
                urls.append(url)
        sub_tit = main_item.find('a').get('title').strip()
        sub_title.append(sub_tit)
        k+=1
    # print(len(urls))
    # print(urls)
    # print(len(sub_title))
    # print(sub_title)
    j=0
    while j < len(urls):
        browser.get(urls[j])
        if j < 3:
            category = sub_title[j]
            try:
                wait.until(lambda browser: browser.find_elements_by_css_selector("#div_Danh_Sach_San_Pham > div.ProductList3Col_item"))
                elem = browser.find_element_by_xpath('//*[@id="div_Danh_Sach_San_Pham_loadMore_btn"]/a')
                while elem.is_displayed():
                    time.sleep(1)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1
        else:
            category = sub_title[len(sub_title)-1]
            try:
                wait.until(lambda browser: browser.find_elements_by_css_selector("#div_Danh_Sach_San_Pham > span.list-pk-item"))
                elem = browser.find_element_by_xpath('//*[@id="div_Danh_Sach_San_Pham_loadMore_btn"]/a')
                while elem.is_displayed():
                    time.sleep(1)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1

        # print(page_count)

        if j < 3:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', id='div_Danh_Sach_San_Pham').find_all('div', class_='ProductList3Col_item')
            # print("If")
            # print(len(list))
            # print(list)
            # elements = browser.find_elements_by_css_selector("#div_Danh_Sach_San_Pham > div.ProductList3Col_item")
            # print(len(elements))
            # print(elements)
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.find('a').get('data-pid').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                # try:
                #     brand = item.find('div', class_='manuface').find('a').get('title').text.strip()
                # except:
                #     brand = None
                if item.find('h2', class_='name') != None:
                    title_Vietnamese = item.find('h2', class_='name').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('span', class_='price') != None:
                    price = item.find('span', class_='price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                try:
                    old_price = item.find('div', class_='sell').find('span').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                except:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'id': item_id,
                        'good_name': title_Vietnamese,
                        # 'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_"
            write_html(browser.page_source, file_name)
        else:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', id='div_Danh_Sach_San_Pham').find_all('span', class_='list-pk-item')
            # print("Else")
            # print(len(list))
            # print(list)
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.select('div.item-pk-sale > a')[1]
                item_id = item_id.get('href')
                item_id = item_id.split('-pid')[1]
                item_id = item_id.replace('.html','')
                item_id = item_id.strip()
                # Vietnamese
                # English
                # try:
                #     brand = item.find('div', class_='manuface').find('a').get('title').text.strip()
                # except:
                #     brand = None
                if item.find('div', class_='name-pk') != None:
                    title_Vietnamese = item.find('div', class_='name-pk').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('span', class_='price') != None:
                    price = item.find('span', class_='price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='price-old') != None:
                    old_price = item.find('span', class_='price-old').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'id': item_id,
                        'good_name': title_Vietnamese,
                        # 'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_"
            write_html(browser.page_source, file_name)
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
