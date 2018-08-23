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
from selenium.webdriver.chrome.options import Options


SITE_NAME = "vuivui"
BASE_URL = "https://www.vuivui.com"
PROJECT_PATH = re.sub("/py/.+", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38
# prefs = {"profile.managed_default_content_settings.images":2}
# OPTIONS.add_experimental_option("prefs",prefs)


def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'sub_category', 'id', 'good_name', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['sub_category'], data['id'], data['good_name'], data['brand'], data['price'],data['old_price'], data['date']))


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
    main_category_list = soup.find('div', class_='wrap').find_all('a', class_='item')
    write_html(browser.page_source, "All_cat_")
    for main_item in main_category_list:
        href = BASE_URL + main_item.get('href')
        browser.get(href)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        category_list = soup.find('div', class_='mnu-ct').find_all('div', class_='item')
        for item in category_list:
            url_list = item.find_all('a')
            for url in url_list:
                hre = url.get('href')
                if "#" in hre:
                    continue
                else:
                    urls.append(BASE_URL + str(hre))
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        browser.get(urls[j])
        time.sleep(5)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        try:
            category_titles = soup.find('nav', class_='bread').find_all('a', class_='item')
            if len(category_titles) == 2:
                category = category_titles[1].text.strip()
                sub_category = None
            if len(category_titles) == 3:
                category = category_titles[1].text.strip()
                sub_category = category_titles[2].text.strip()
            if len(category_titles) == 4:
                category = category_titles[1].text.strip()
                sub_category = category_titles[2].text.strip()
        except:
            j+=1
            continue

        # print(page_count)

        i=0
        local_title = True
        while local_title:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                browser.get(urls[j] + "?page=" + str(i))
                time.sleep(1)
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="page-next"]'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='itmpro')
            if i == 0:
                time.sleep(1)
                # wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="page-next"]'))
                wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[3]'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='itmpro')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = BASE_URL + item.find('a').get('href').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                try:
                    brand = item.find('div', class_='manuface').find('a').get('title').text.strip()
                except:
                    brand = None
                if item.find('div', class_='riki-name') != None:
                    title_Vietnamese = item.find('div', class_='riki-name').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('div', class_='pricenew') != None:
                    price = item.find('div', class_='pricenew').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('div', class_='priceline') != None:
                    old_price = item.find('div', class_='priceline').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'sub_category': sub_category,
                        'id': item_id,
                        'good_name': title_Vietnamese,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if soup.find('div', class_='pagination') == None:
                break
            if soup.find('a', id='page-next').has_attr('class'):
                i+=1
                continue
            else:
                break
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
