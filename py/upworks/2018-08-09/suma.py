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
from selenium.webdriver.support.ui import Select



SITE_NAME = "suma"
BASE_URL = "https://suma.vn"
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
            writer.writerow(('category', 'id', 'title', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['title'], data['brand'], data['price'], data['old_price'], data['date']))

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
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    urls = []
    globals_url = ['https://suma.vn/ho-chi-minh-city_suma', 'https://suma.vn/vi/ho-chi-minh-city_suma']
    for url in globals_url:
        browser.get(url)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        menu_list = soup.find('div', class_='nav-categories').find_all('div', class_='cate-item')
        for menu_item in menu_list:
            href = BASE_URL + menu_item.find('a').get('href')
            if href not in urls:
                urls.append(href)
    write_html(browser.page_source, "All_cat_")
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')
        category = soup.find('h3', class_='title-cate').text.strip()


        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            try:
                elem = browser.find_element_by_xpath('//*[@id="load_more"]/a')
                while elem.is_displayed():
                    time.sleep(1)
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', id='list_items').find_all('div', class_='product-item')
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a') == None:
                    continue
                item_id = BASE_URL + item.find('a').get('href').strip()

                # ---price, 
                # ---old_price (previous price if exists), 
                # ---good_name_english (name of product in English - if available),
                # ---good_name (name of product in Vietnamese),
                # ---11111111111111111id (product_id by seller - could be created from the link),
                # ---11111111111111111category (name of category),
                # ---brand (if available),
                # ---111111111111111111date (current date),
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('p', class_='cate-name') != None:
                    brand = item.find('p', class_='cate-name').text.strip()
                else:
                    brand = None

                if item.find('p', class_='product-name') != None:
                    title = item.find('p', class_='product-name').text.strip()
                else:
                    title = None
                # if item.find('div', class_='english_name') != None:
                #     title_Vietnamese = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_Vietnamese = None
                # print("Title: " + title)
                if item.find('p', class_='product-price') != None:
                    price = item.find('p', class_='product-price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='old-price') != None:
                    old_price = item.find('span', class_='old-price').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'id': item_id,
                        'title': title,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
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
