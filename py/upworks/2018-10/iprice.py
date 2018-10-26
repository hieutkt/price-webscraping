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



SITE_NAME = "iprice"
BASE_URL = "https://iprice.vn"
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
            writer.writerow(('category', 'name', 'seller', 'price', 'old_price', 'date'))
        writer.writerow((data['category'], data['name'], data['seller'], data['price'], data['old_price'], data['date']))

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
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,30)
    urls = []
    titles = []
    browser.get('https://iprice.vn/categories/')
    soup = BeautifulSoup(browser.page_source, 'lxml')
    write_html(browser.page_source, "All_cat_")
    elements = browser.find_elements_by_css_selector('#categories > ul > li > a')
    # print(len(elements))
    for item in elements:
        href = item.get_attribute("href")
        title = item.text.strip()
        if href not in urls:
            urls.append(href)
            titles.append(title)
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        sys.stdout.write('\rScraping ' + urls[j] + '...' + ' ' * 30)
        browser.get(urls[j])
        category = titles[j]
        # print(page_count)
        href=''
        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#pagination > ul'))
                    elements = browser.find_elements_by_css_selector('#pagination > ul > li')
                    class_name = [e.find_element_by_css_selector('a').get_attribute('class') for e in elements]
                    page_current_index = ['selected' in a for a in class_name].index(True)
                    page_next_index = page_current_index + 1
                    if page_next_index < len(elements):
                        page_next_url = elements[page_next_index].find_element_by_css_selector('a').get_attribute('href')
                        sys.stdout.write('\rScraping ' + page_next_url + '...')
                        browser.get(page_next_url)
                    else:
                        pagination = False
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
                try:
                    # time.sleep(5)
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    div_list = soup.find('div', class_='product-list').find_all('div', class_='pu')
                    # list = browser.find_elements_by_css_selector('#shop > div > div > div > div')
                except:
                    pagination = False
            if i == 0:
                try:
                    # time.sleep(5)
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    div_list = soup.find('div', class_='product-list').find_all('div', class_='pu')
                    # list = browser.find_elements_by_css_selector('#shop > div > div > div > div')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(list)
            # print('11111111111111111')
            # print(i+1)
            p=0
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            for item in div_list:
                # try:
                #     href = item.find_element_by_css_selector('a.db').get_attribute("href")
                #     browser.get(href)
                #     soup = BeautifulSoup(browser.page_source, 'lxml')
                # except:
                #     continue

                # ---name,
                # ---price,
                # ---seller 
                # ---old_price (previous price if exists),
                # ---category (name of category),
                # ---current date

                try:
                    price = item.find('span', class_='accent').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                except:
                    price = None
                    continue

                # try:
                #     name = soup.find('h1', class_='tl').text.strip()
                # except:
                #     continue
                name=''
                try:
                    name = item.find('div', class_='name').text.strip()
                except:
                    # print(3243)
                    name=''
                    # continue
                if name == '':
                    try:
                        name = item.find('span', class_='name').text.strip()
                    except:
                        # print(3243)
                        name=''
                        # continue

                if name == '':
                    # print(3243)
                    p+=1
                    continue


                try:
                    old_price = item.find('span', class_='original').text.strip()
                except:
                    old_price = None

                stores =  item.find('figcaption').find_all('a', class_='store')

                for store in stores:
                    seller = store.get('data-vars-merchant').split('|')[0]
                    price = store.find('div', class_='s-p').text.strip()
                    data = {'category': category,
                            'name': name,
                            'seller': seller,
                            'price': price,
                            'old_price': old_price,
                            'date': DATE}
                    write_csv(data)

                stores =  item.find('figcaption').find_all('div', class_='store')
                # print(len(stores))
                # print(stores)

                for store in stores:
                    seller = store.find('div', class_='f13').find('strong').text.strip()
                    # price = store.find('div', class_='s-p').text.strip()
                    data = {'category': category,
                            'name': name,
                            'seller': seller,
                            'price': price,
                            'old_price': old_price,
                            'date': DATE}
                    write_csv(data)

                # ar = soup.find('div', id='main-accordion_AMP_content_0').find_all('div', class_='offers-collection')
                # for a in ar:
                #     seller = a.find('strong', class_='blue').text.strip()
                #     price = a.find('div', class_='green').text.strip()
                #     data = {'category': category,
                #             'name': name,
                #             'seller': seller,
                #             'price': price,
                #             'old_price': old_price,
                #             'date': DATE}
                #     write_csv(data)
            i+=1
            # print(len(list)-p)
        j+=1
    browser.quit()
    compress_data()
    sys.stdout.write('\r' + DATE + ': Compressed, hibernating...')

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
