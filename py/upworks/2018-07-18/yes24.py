from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import schedule
import zipfile

SITE_NAME = "yes24"
BASE_URL = "https://www.yes24.vn"
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
    main_category_list = soup.find('div', id='menu-bottom').find('ul', class_='tr-list-menu').find_all('div', class_='tr-submenu')
    for main_item in main_category_list:
        category_list = main_item.find('ul', class_='tr-list-ds-con').find_all('li')
        for item in category_list:
            url = item.find('a').get('href')
            urls.append(url)
# cat-tree-nav
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category_titles = soup.find('div', class_='th-breadcrumb').find_all('li')
        if len(category_titles) == 2:
            category = category_titles[1].find('a').text.strip()
            sub_category = None
        if len(category_titles) == 3:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()
        if len(category_titles) == 4:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()

        soup = BeautifulSoup(browser.page_source, 'lxml')
        try:
            page_count = soup.find('ul', class_='th-paging').find_all('li')
            page_count = page_count[len(page_count)-2]
            page_count = page_count.find('a').text.strip()
        except:
            page_count = "1"

        i=0
        # th-paging
        while i < int(page_count)+1:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                elements = browser.find_elements_by_css_selector('ul.th-paging > li')
                c=0
                while c < len(elements):
                    try:
                        element = elements[c].find_element_by_css_selector('a.active')
                    except NoSuchElementException:
                        c+=1
                        continue
                    # element = browser.find_element_by_xpath('/html/body/div[3]/div/div[2]/div/ul[2]')
                    # actions = ActionChains(browser)
                    # actions.move_to_element(element).perform()
                    element = elements[c+1].find_element_by_css_selector('a')
                    browser.execute_script("arguments[0].click();", element)
                    # elements[c+1].click()
                    break
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('li.th-product-item-wrap'))
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find_all('li', class_='th-product-item-wrap')
                except TimeoutException:
                    i+=1
                    continue
                except NoSuchElementException:
                    i+=1
                    continue
                except StaleElementReferenceException:
                    i+=1
                    continue
                except:
                    i+=1
                    continue
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('li', class_='th-product-item-wrap')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.find('a').get('href').strip()
                # https://www.yes24.vn/bo-suu-tap-quan-ao-nu-han-quoc-thoi-trang-jcstyle-p1926881.html
                item_id = item_id.split('-p')
                item_id = item_id[len(item_id)-1]
                item_id = item_id.replace('.html', '').strip()
                # Vietnamese
                # English
                if item.find('div', class_='th-product-info') != None:
                    brand = item.find('div', class_='th-product-info').find('a').text.strip()
                else:
                    brand = None
                if item.find('h3') != None:
                    title_Vietnamese = item.find('h3').find('a').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('span', class_='th-product-price-new') != None:
                    price = item.find('span', class_='th-product-price-new').text.strip()
                    price = price.split('đ')[0]
                    price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='th-product-price-old') != None:
                    old_price = item.find('span', class_='th-product-price-old').text.strip()
                    old_price = old_price.split('đ')[0]
                    old_price = old_price.strip()
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
