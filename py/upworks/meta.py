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

SITE_NAME = "meta"
BASE_URL = "https://meta.vn"
PROJECT_PATH = re.sub('/py/upworks$', '', os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"


def write_csv(data):
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, delimiter=',')
        writer.writerow(data)

def write_html(html, file_name):
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    browser.get(BASE_URL)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    urls = []
    main_category_list = soup.find('ul', id='main-smart-menu').find_all('li', class_='menu-item')
    write_html(browser.page_source, "All_cat_")
    k=1
    for main_item in main_category_list:
        if k >= 12:
            break
        href = BASE_URL + main_item.find('a').get('href')
        browser.get(href)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        category_list = soup.find('ul', class_='cat-tree-nav').find_all('li', class_='cat-tree-item')
        for item in category_list:
            url = BASE_URL + item.find('a').get('href')
            urls.append(url)
        k+=1
# cat-tree-nav
    j=0
    while j < len(urls):
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category_titles = soup.find('ol', class_='breadcrum').find_all('li', class_='breadcrum-item')
        if len(category_titles) == 2:
            category = category_titles[1].find('a').text.strip()
            sub_category = None
        if len(category_titles) == 3:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()
        if len(category_titles) == 4:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()

        # print(page_count)

        i=0
        local_title = 5
        while i < int(local_title):
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                browser.get(urls[j] + "?p=" + str(i+1))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='product-catalog-item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='product-catalog-item')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.get('data-pid').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('div', class_='name-brand') != None:
                    brand = item.find('div', class_='name-brand').text.strip()
                else:
                    brand = None
                if item.find('div', class_='home-product-title') != None:
                    title_Vietnamese = item.find('div', class_='home-product-title').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('span', class_='list-product-meta-price') != None:
                    price = item.find('span', class_='list-product-meta-price').text.strip()
                    price = price.split('đ')[0]
                    price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='list-product-old-price') != None:
                    old_price = item.find('span', class_='list-product-old-price').text.strip()
                    old_price = old_price.split('đ')[0]
                    old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'sub_category': sub_category,
                        'id': item_id,
                        'title_Vietnamese': title_Vietnamese,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if soup.find('div', class_='list-pagination') == None:
                break
            page_count = soup.find('div', class_='list-pagination').find_all('a')
            local_title = browser.find_element_by_xpath('//*[@id="_products"]/div/div[2]/div/a[' + str(len(page_count)) + ']')
            local_title = local_title.get_attribute('title')
            local_title = local_title.split('Xem trang')[1]
            local_title = local_title.strip()
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

if "test" in sys.agrv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)
