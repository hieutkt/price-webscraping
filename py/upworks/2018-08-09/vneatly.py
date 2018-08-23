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



SITE_NAME = "vneatly"
BASE_URL = "https://vneatly.com"
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
            writer.writerow(('category', 'product_name', 'brand', 'availability', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['product_name'], data['brand'], data['availability'], data['price'], data['old_price'], data['date']))

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
    browser.get(BASE_URL)
    urls = []
    write_html(browser.page_source, "All_cat_")
    soup = BeautifulSoup(browser.page_source, 'lxml')
    main_list = soup.find('ul', class_='nav-verticalmenu').find_all('li')
    k=0
    for main_item in main_list:
        href = BASE_URL + main_item.find('a').get('href')
        browser.get(href)
        if k >= 1:
            break
        soup = BeautifulSoup(browser.page_source, 'lxml')
        list = soup.find('ul', class_='listSidebar').find_all('li')
        for item in list:
            if item.find('span', class_='pull-right') == None:
                continue
            else:
                url = BASE_URL + item.find('a').get('href')
                if url not in urls:
                    urls.append(url)
        k+=1

    j=0
    while j < len(urls):
        browser.get(urls[j])

        soup = BeautifulSoup(browser.page_source, 'lxml')
        category_titles = soup.find('ol', class_='breadcrumb').find_all('li')
        if len(category_titles) == 2:
            category = category_titles[1].find('span').text.strip()
        else:
            category = category_titles[1].find('span').text.strip()

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait2.until(lambda browser: browser.find_element_by_css_selector('#pagination > ul'))
                    elements = browser.find_elements_by_css_selector('#pagination > ul > li')
                    c=0
                    while c < len(elements)-1:
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-2 >= c+1:
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
                    list = soup.find('div', class_='product_list').find_all('div', class_='product_block')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='product_list').find_all('div', class_='product_block')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a', class_='product-name') == None:
                    continue
                else:
                    href = BASE_URL + item.find('a', class_='product-name').get('href')
                    browser2.get(href)
                
                soup = BeautifulSoup(browser2.page_source, 'lxml')
                
                if soup.find('h1', itemprop='name') != None:
                    product_name = soup.find('h1', itemprop='name').text.strip()
                else:
                    product_name = None

                # ---brand, (shown as Nhãn hiệu) 
                # ---availability (shown as Tình trạng)
                # ---delivery fee, (if exists)
                # ---1111111111product name,
                # ---111111111price,
                # ---1111111111old_price (previous price if exists),
                # ---1111111111category (name of category),
                # ---1111111111current date

                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if soup.find('span', class_='price') != None:
                    price = soup.find('span', class_='price').text.strip()
                    # price = price.split('₫')[1]
                    # price = price.strip()
                else:
                    price = None

                if soup.find('span', class_='availability') != None:
                    availability = soup.find('span', class_='availability').text.strip()
                else:
                    availability = None
                # print("Price: " + str(price))
                if soup.find('span', class_='product-price-old') != None:
                    old_price = soup.find('span', class_='product-price-old').text.strip()
                    # old_price = old_price.split('₫')[1]
                    # old_price = old_price.strip()
                else:
                    old_price = None

                brand = None
                # availability = None
                m_list = soup.find('ul', class_='description').find_all('li')[0]
                brand = m_list.find('a').text.strip()

                data = {'category': category,
                        'product_name': product_name,
                        'brand': brand,
                        'availability': availability,
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
