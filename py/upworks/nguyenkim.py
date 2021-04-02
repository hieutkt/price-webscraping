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
from selenium.webdriver.chrome.options import Options
import signal


SITE_NAME = "nguyenkim"
BASE_URL = "https://www.nguyenkim.com"
PROJECT_PATH = re.sub('/py/upworks$', '', os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"


# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--no-sandbox') # Bypass OS security model
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
            writer.writerow(('category', 'id', 'good_name', 'brand', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['id'], data['good_name'], data['brand'], data['price'],data['old_price'], data['date']))


def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    browser = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               options=OPTIONS)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    urls = []
    browser.get(BASE_URL)
    wait.until(lambda browser: browser.find_element_by_css_selector('#nk-danh-muc-san-pham-left > ul > li'))
    elements = browser.find_elements_by_css_selector('#nk-danh-muc-san-pham-left > ul > li')
    write_html(browser.page_source, "All_cat_")
    c=1
    k=0
    j=0
    while c < len(elements):
        if c==4:
            c+=1
            continue
        if j != 0:
            browser.get(BASE_URL)
            wait.until(lambda browser: browser.find_element_by_css_selector('#nk-danh-muc-san-pham-left > ul > li'))
            elements = browser.find_elements_by_css_selector('#nk-danh-muc-san-pham-left > ul > li')
        hover = ActionChains(browser).move_to_element(elements[c])
        hover.perform()
        time.sleep(1)
        #nk-danh-muc-san-pham-left > ul > li:nth-child(2) > div.sub-menu.may-lanh > div
        spans = browser.find_elements_by_css_selector('#nk-danh-muc-san-pham-left > ul > li:nth-child(' + str(c+1) + ') h3 span.js_hidden_link')
        if len(spans) > 0:
            browser.execute_script("arguments[0].click();", spans[k])
        # spans[k].click()
            if browser.current_url not in urls:
                urls.append(browser.current_url)
                # print(browser.current_url)
        k+=1
        j+=1
        if k >= len(spans):
            k=0
            c+=1
    # print(urls)
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category_titles = soup.find('div', class_='breadcrumbs').find_all('li')
        if len(category_titles) == 2:
            category = category_titles[1].find('a').text.strip()
        if len(category_titles) == 3:
            category = category_titles[1].find('a').text.strip()
        if len(category_titles) == 4:
            category = category_titles[1].find('a').text.strip()

        # print(page_count)

        i=0
        # //*[@id="feature-product-grid"]/div[4]/div[3]/a
        #feature-product-grid > div.ty-pagination.NkReview_footer.clearfix > div.NkReview_footer_col-3 > a
        if soup.find('span', class_='ty-pagination__text') != None:
            pagination = soup.find('span', class_='ty-pagination__text').text.strip()
            pagination = pagination.split('số')
            pagination = pagination[len(pagination)-1]
            pagination = pagination.strip()
        else:
            pagination = 1
        while i < int(pagination):
            if i != 0:
                browser.get(urls[j] + "page-" + str(i+1) + "/")
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', id='pagination_contents').find_all('div', class_='nk-fgp-items')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', id='pagination_contents').find_all('div', class_='nk-fgp-items')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.get('id').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('strong', class_='brand') != None:
                    brand = item.find('strong', class_='brand').text.strip()
                else:
                    brand = None
                if item.find('div', class_='label') != None:
                    title_Vietnamese = item.find('div', class_='label').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('p', class_='price discount') != None:
                    price = item.find('p', class_='price discount').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('p', class_='price strike') != None:
                    old_price = item.find('p', class_='price strike').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None

                date = DATE

                data = {'category': category,
                        # 'sub_category': sub_category,
                        'id': item_id,
                        'good_name': title_Vietnamese,
                        'brand': brand,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            i+=1
        j+=1
    # Close browser
    browser.close()
    browser.service.process.send_signal(signal.SIGTERM)
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)
