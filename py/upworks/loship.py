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



SITE_NAME = "loship"
BASE_URL = "https://loship.vn"
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
            writer.writerow(('seller', 'address', 'delivery_fee', 'food_category', 'food_name', 'food_order', 'food_price', 'date'))
        writer.writerow((data['seller'], data['address'], data['delivery_fee'], data['food_category'], data['food_name'], data['food_order'], data['food_price'], data['date']))

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
    chromeOptions.add_argument('--no-sandbox') # Bypass OS security model
    chromeOptions.add_experimental_option("prefs",prefs)
    browser2 = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,30)
    wait3 = ui.WebDriverWait(browser2,60)
    urls = ['https://loship.vn/ha-noi/danh-sach-dia-diem-giao-tan-noi', 'https://loship.vn/ho-chi-minh/danh-sach-dia-diem-giao-tan-noi']
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])

        # category = titles[j]


        # print(page_count)

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#screen > div > div > div > div.container > div > div.pagination > ul'))
                    elements = browser.find_elements_by_css_selector('#screen > div > div > div > div.container > div > div.pagination > ul > li')
                    # browser.get(urls[j]+'?page='+str(i+1))
                    c=0
                    while c < len(elements):
                        class_name = elements[c].get_attribute("class")
                        if "current" in class_name:
                            if len(elements)-1 >= c+1:
                                # href_glob = elements[c+1].find_element_by_css_selector('a').get_attribute("href")
                                # browser.get(href_glob)
                                # hover = ActionChains(browser).move_to_element(elements[c+1])
                                # hover.perform()
                                browser.execute_script("arguments[0].click();", elements[c+1])
                                # elements[c+1].click()
                                time.sleep(7)
                                wait.until(lambda browser: browser.find_element_by_css_selector('#screen > div > div > div > div.container > div > div.merchant-list > div.item'))
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
                    list = soup.find('div', class_='merchant-list').find_all('div', class_='item')
                except:
                    pagination = False
            if i == 0:
                try:
                    time.sleep(7)
                    wait.until(lambda browser: browser.find_element_by_css_selector('#screen > div > div > div > div.container > div > div.merchant-list > div.item'))
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='merchant-list').find_all('div', class_='item')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                try:
                    href = BASE_URL + item.find('a').get('href')
                    browser2.get(href)
                    wait3.until(lambda browser2: browser2.find_element_by_css_selector('#screen > div > div > div.container > div.page-merchant > div.col-left > div.mc-menu > div.submenu-content-list'))
                    try:
                        elem = browser2.find_element_by_css_selector('#screen > div > div > div.container > div.page-merchant > div.col-left > div.mc-menu > div.submenu-content-list > div:nth-child(3) > div > a')
                        while elem.is_displayed():
                            time.sleep(1.5)
                            browser2.execute_script("arguments[0].click();", elem)
                            time.sleep(1.5)
                    except NoSuchElementException:
                        k=1
                    except StaleElementReferenceException:
                        k=1
                except:
                    continue
                soup = BeautifulSoup(browser2.page_source, 'lxml')

                # ---seller,
                # ---address
                # ---delivery_fee
                # ---food_name
                # ---food_order
                # ---food_price
                # ---food_category (name of category),
                # ---current date


                try:
                    address = soup.find('h2', class_='address-text').text.strip()
                except:
                    address = None

                try:
                    seller = soup.find('h1', class_='name').text.strip()
                except:
                    seller = None

                try:
                    delivery_fee = soup.find('span', itemprop='priceRange').text.strip()
                except:
                    delivery_fee = None

                menu = soup.find('div', class_='submenu-content-list').find_all('div', class_='mc-submenu')
                for menu_item in menu:
                    food_category = menu_item.find('h3').text.strip()
                    food_list = menu_item.find('ul', class_='food-list').find_all('li')
                    for food in food_list:
                        food_price = food.find('div', class_='price').text.strip()
                        food_name = food.find('div', class_='name').text.strip()
                        food_order = food.find('div', class_='total-count').text.strip()
                        data = {'seller': seller,
                                'address': address,
                                'delivery_fee': delivery_fee,
                                'food_category': food_category,
                                'food_name': food_name,
                                'food_order': food_order,
                                'food_price': food_price,
                                'date': DATE}
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
