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



SITE_NAME = "chonmon"
BASE_URL = "https://chonmon.vn"
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
            writer.writerow(('location', 'restaurant_name', 'restaurant_address', 'food_category', 'food_name', 'food_price', 'date'))
        writer.writerow((data['location'], data['restaurant_name'], data['restaurant_address'], data['food_category'], data['food_name'], data['food_price'], data['date']))


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
    # print(len(urls))
    # print(urls)
    j=0
    while j < 2:
        if j == 0:
            try:
                browser.get(BASE_URL)
                elem = browser.find_element_by_xpath('//*[@id="province-modal"]/div/div/div/div/div/div[2]/select/option[2]')
                value = elem.get_attribute("value")
                location = elem.text.strip()
                select = Select(browser.find_element_by_xpath('//*[@id="province-modal"]/div/div/div/div/div/div[2]/select'))
                select.select_by_value(value)
                elem = browser.find_element_by_xpath('//*[@id="province-modal"]')
                while elem.is_displayed():
                    time.sleep(1)
                time.sleep(10)
            except StaleElementReferenceException:
                write_html(browser.page_source, "All_cat_")
            write_html(browser.page_source, "All_cat_")
        else:
            browser.get(BASE_URL)
            elem = browser.find_element_by_xpath('//*[@id="js_web_province"]/option[2]')
            value = elem.get_attribute("value")
            location = elem.text.strip()
            select = Select(browser.find_element_by_xpath('//*[@id="js_web_province"]'))
            select.select_by_value(value)
            time.sleep(10)


        # print(page_count)

        i=0
        local_title = 1
        while i < int(local_title):
            elem = browser.find_element_by_xpath('//*[@id="page-content"]/div/div[2]/div[3]/a')
            href = elem.get_attribute("href")
            browser.get(href)
            try:
                elem = browser.find_element_by_xpath('//*[@id="page-content"]/div/div/div[4]/div[2]/a')
                while elem.is_displayed():
                    time.sleep(1)
                    # actions = ActionChains(browser)
                    # actions.move_to_element(elem).perform()
                    # elem.click()
                    browser.execute_script("arguments[0].click();", elem)
                    time.sleep(1)
            except NoSuchElementException:
                k=1
            except StaleElementReferenceException:
                k=1
            soup = BeautifulSoup(browser.page_source, 'lxml')
            list = soup.find('div', class_='box-deals').find_all('div', class_='box-deal')
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('a') == None:
                    continue
                href = item.find('a').get('href')
                browser2.get(href)
                soup = BeautifulSoup(browser2.page_source, 'lxml')

                # ---11111111111restaurant name,
                # ---111111111111111restaurant address,
                # ---delivery fee, (if exists)
                # ---food name,
                # ---food price,
                # ---food category,
                # ---1111111111111111location (chosen location),
                # ---1111111111111111current date
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English

                if soup.find('div', class_='res-title') != None:
                    restaurant_name = soup.find('div', class_='res-title').text.strip()
                else:
                    restaurant_name = None

                if soup.find('span', class_='info-label') != None:
                    restaurant_address = soup.find('span', class_='info-label').text.strip()
                else:
                    restaurant_address = None

                main_food_list = soup.find_all('div', class_='box-menu-lists')
                for main_food_item in main_food_list:
                    food_category = main_food_item.find('div', class_='menu-list-title').text.strip()
                    food_list = soup.find('ul', class_='menu-lists').find_all('li', class_='menu-list-item')
                    for food_item in food_list:
                        food_name = soup.find('div', class_='list-item-title').text.strip()
                        food_price = soup.find('div', class_='list-item-price').text.strip()
                        data = {'location': location,
                                'restaurant_name': restaurant_name,
                                'restaurant_address': restaurant_address,
                                'food_category': food_category,
                                'food_name': food_name,
                                'food_price': food_price,
                                'date': DATE}
                        write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            i+=1
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
