from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
import random
import zipfile
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select



SITE_NAME = "vietnammm"
BASE_URL = "https://www.vietnammm.com/en/"
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
            writer.writerow(('location', 'restaurant_name', 'restaurant_address', 'delivery_fee', 'minimum_order', 'delivery_coverage', 'food_category', 'food_name', 'food_price', 'date'))
        writer.writerow((data['location'], data['restaurant_name'], data['restaurant_address'], data['delivery_fee'], data['minimum_order'], data['delivery_coverage'],data['food_category'], data['food_name'], data['food_price'], data['date']))


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
    chromeOptions.add_experimental_option("prefs",prefs)
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument("disable-infobars")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    browser.get(BASE_URL)
    urls = []
    urls = ['https://www.vietnammm.com/en/order-takeaway-cam-le', 'https://www.vietnammm.com/en/order-takeaway-hai-chau', 'https://www.vietnammm.com/en/order-takeaway-hoa-vang', 'https://www.vietnammm.com/en/order-takeaway-lien-chieu', 'https://www.vietnammm.com/en/order-takeaway-ngu-hanh-son', 'https://www.vietnammm.com/en/order-takeaway-son-tra', 'https://www.vietnammm.com/en/order-takeaway-thanh-khe', 'https://www.vietnammm.com/en/order-takeaway-ba-dinh', 'https://www.vietnammm.com/en/order-takeaway-cau-giay', 'https://www.vietnammm.com/en/order-takeaway-dong-da', 'https://www.vietnammm.com/en/order-takeaway-ha-dong', 'https://www.vietnammm.com/en/order-takeaway-hai-ba-trung', 'https://www.vietnammm.com/en/order-takeaway-hoang-mai', 'https://www.vietnammm.com/en/order-takeaway-hoan-kiem', 'https://www.vietnammm.com/en/order-takeaway-long-bien', 'https://www.vietnammm.com/en/order-takeaway-tay-ho', 'https://www.vietnammm.com/en/order-takeaway-thanh-xuan', 'https://www.vietnammm.com/en/order-takeaway-tu-liem', 'https://www.vietnammm.com/en/order-takeaway-an-phu-thao-dien', 'https://www.vietnammm.com/en/order-takeaway-binh-chanh-district', 'https://www.vietnammm.com/en/order-takeaway-binh-tan-district', 'https://www.vietnammm.com/en/order-takeaway-binh-thanh-district', 'https://www.vietnammm.com/en/order-takeaway-district-1', 'https://www.vietnammm.com/en/order-takeaway-district-2', 'https://www.vietnammm.com/en/order-takeaway-district-3', 'https://www.vietnammm.com/en/order-takeaway-district-4', 'https://www.vietnammm.com/en/order-takeaway-district-5', 'https://www.vietnammm.com/en/order-takeaway-district-6', 'https://www.vietnammm.com/en/order-takeaway-district-7', 'https://www.vietnammm.com/en/order-takeaway-district-8', 'https://www.vietnammm.com/en/order-takeaway-district-9', 'https://www.vietnammm.com/en/order-takeaway-district-10', 'https://www.vietnammm.com/en/order-takeaway-district-11', 'https://www.vietnammm.com/en/order-takeaway-district-12', 'https://www.vietnammm.com/en/order-takeaway-go-vap-district', 'https://www.vietnammm.com/en/order-takeaway-phu-my-hung', 'https://www.vietnammm.com/en/order-takeaway-phu-nhuan-district', 'https://www.vietnammm.com/en/order-takeaway-tan-binh-district', 'https://www.vietnammm.com/en/order-takeaway-tan-phu-district', 'https://www.vietnammm.com/en/order-takeaway-thu-duc-district', 'https://www.vietnammm.com/en/order-takeaway-dien-duong', 'https://www.vietnammm.com/en/order-takeaway-hoi-an-town', 'https://www.vietnammm.com/en/order-takeaway-biet-thu-area', 'https://www.vietnammm.com/en/order-takeaway-hung-vuong-area', 'https://www.vietnammm.com/en/order-takeaway-loc-tho-ward', 'https://www.vietnammm.com/en/order-takeaway-nguyen-thien-thuat-area', 'https://www.vietnammm.com/en/order-takeaway-ngoc-hiep-ward', 'https://www.vietnammm.com/en/order-takeaway-phuoc-hai-ward', 'https://www.vietnammm.com/en/order-takeaway-phuoc-hoa-ward', 'https://www.vietnammm.com/en/order-takeaway-phuoc-tan-ward', 'https://www.vietnammm.com/en/order-takeaway-phuoc-tien-ward', 'https://www.vietnammm.com/en/order-takeaway-tran-phu', 'https://www.vietnammm.com/en/order-takeaway-tran-quang-khai-area', 'https://www.vietnammm.com/en/order-takeaway-van-thang-ward']
    # values = []
    # values2 = []
    # wait.until(lambda browser: browser.find_elements_by_css_selector('#isearchstring1 > option'))
    # elements = browser.find_elements_by_css_selector('#isearchstring1 > option')
    # write_html(browser.page_source, "All_cat_")
    # c=0
    # k=0
    # while c < len(elements):
    #     if c == 0:
    #         c+=1
    #         continue
    #     try:
    #         value = elements[c].get_attribute("value")
    #     except StaleElementReferenceException:
    #         k+=1
    #         if k < 10:
    #             continue
    #         else:
    #             k=0
    #             c+=1
    #             continue
    #     values.append(value)
    #     c+=1
    #     # print(value)
    # # k=0
    # # old_elements2 = []
    # for gvalue in values:
    #     try:
    #         wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="isearchstring1"]'))
    #     except TimeoutException:
    #         browser.refresh()
    #         try:
    #             wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="isearchstring1"]'))
    #         except TimeoutException:
    #             continue
    #     select = Select(browser.find_element_by_xpath('//*[@id="isearchstring1"]'))
    #     try:
    #         select.select_by_value(gvalue)
    #     except StaleElementReferenceException:
    #         try:
    #             select.select_by_value(gvalue)
    #         except StaleElementReferenceException:
    #             try:
    #                 select.select_by_value(gvalue)
    #             except StaleElementReferenceException:
    #                 try:
    #                     select.select_by_value(gvalue)
    #                 except StaleElementReferenceException:
    #                     try:
    #                         select.select_by_value(gvalue)
    #                     except StaleElementReferenceException:
    #                         continue
    #     except:
    #         continue
    #     time.sleep(10)
    #     try:
    #         wait.until(lambda browser: browser.find_elements_by_css_selector('#isearchstring2 > option'))
    #     except TimeoutException:
    #         continue
    #     elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     # print(k)
    #     # if k == 0:
    #     #     wait.until(lambda browser: browser.find_elements_by_css_selector('#isearchstring2 > option'))
    #     #     elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     #     old_elements2 = elements2
    #     # else:
    #     #     wait.until(lambda browser: browser.find_elements_by_css_selector('#isearchstring2 > option'))
    #     #     elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     #     # print(old_elements2)
    #     #     while old_elements2 == elements2:
    #     #         time.sleep(1)
    #     #         elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     #     old_elements2 = elements2
    #     #     elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     # print(elements2)
    #     while len(elements2) <= 1:
    #         time.sleep(1)
    #         elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #     c=0
    #     for element in elements2:
    #         if c == 0:
    #             c+=1
    #             continue
    #         try:
    #             value = element.get_attribute("value")
    #         except StaleElementReferenceException:
    #             continue
    #         except:
    #             continue
    #         # print(value)
    #         values2.append(value)
    #         c+=1
    #     # print(len(values2))
    #     for value in values2:
    #         el = browser.find_element_by_css_selector('#isearchstring1 > option:nth-child(1)')
    #         if el.is_selected():
    #             select = Select(browser.find_element_by_xpath('//*[@id="isearchstring1"]'))
    #             try:
    #                 select.select_by_value(gvalue)
    #             except StaleElementReferenceException:
    #                 continue
    #             except:
    #                 continue
    #             # select.select_by_value(gvalue)
    #             time.sleep(10)
    #             try:
    #                 wait.until(lambda browser: browser.find_elements_by_css_selector('#isearchstring2 > option'))
    #             except TimeoutException:
    #                 continue
    #             elements2 = browser.find_elements_by_css_selector('#isearchstring2 > option')
    #         select = Select(browser.find_element_by_xpath('//*[@id="isearchstring2"]'))
    #         try:
    #             select.select_by_value(value)
    #         except StaleElementReferenceException:
    #             continue
    #         except:
    #             continue
    #         # select.select_by_value(value)
    #         old_url = browser.current_url
    #         elem = browser.find_element_by_xpath('//*[@id="submit_deliveryarea"]')
    #         browser.execute_script("arguments[0].click();", elem)
    #         # elem.click()
    #         new_url = browser.current_url
    #         c = 0
    #         while old_url == new_url:
    #             time.sleep(1)
    #             new_url = browser.current_url
    #             # browser.execute_script("arguments[0].click();", elem)
    #             if c >= 10:
    #                 elem = browser.find_element_by_xpath('//*[@id="submit_deliveryarea"]')
    #                 if elem.is_displayed():
    #                     browser.execute_script("arguments[0].click();", elem)
    #                     c=0
    #             c+=1
    #         url = browser.current_url
    #         if url not in urls:
    #             urls.append(url)
    #         try:
    #             wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="dropdown-location"]'))
    #         except TimeoutException:
    #             continue
    #         elem = browser.find_element_by_xpath('//*[@id="dropdown-location"]')
    #         browser.execute_script("arguments[0].click();", elem)
    #         # browser.get(BASE_URL)
    #     # values2.clear()
    #     values2[:] = []
    #     # old_elements2[:] = []
    #     # k+=1
    # # print(len(urls))
    # # print(urls)
    j=0
    while j < len(urls):
        sys.stdout.write('\rScraping ' + urls[j] + ' ...' + ' '*10)
        browser.get(urls[j])
        try:
            wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="dropdown-location"]/span/span[1]'))
        except TimeoutException:
            continue
        # wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="dropdown-location"]/span/span[1]'))
        location = browser.find_element_by_xpath('//*[@id="dropdown-location"]/span/span[1]').text.strip()
        while location == "":
            time.sleep(1)
            location = browser.find_element_by_xpath('//*[@id="dropdown-location"]/span/span[1]').text.strip()
        location = browser.find_element_by_xpath('//*[@id="dropdown-location"]/span/span[1]').text.strip()

        # location = location.replace(',',' -')
        # if "-" in location:
        #     location = location.split('-')
        #     location = location[1] + location[0]
        # location = location.strip()

        # elements = browser.find_elements_by_css_selector('div.restaurants > div.restaurant')
        soup = BeautifulSoup(browser.page_source, 'lxml')
        glob_list = soup.find('div', class_='restaurants').find_all('div', class_='restaurant')

        i=0
        k=0
        file_name = str(j+1) + "_" + str(i+1) + "_"
        write_html(browser.page_source, file_name)
        for item in glob_list:
            # item = element.get_attribute('innerHTML')
            # item = BeautifulSoup(item, 'lxml')
            # print(item)
            if item.find('a', class_='restaurantname') == None:
                continue
            else:
                url = "https://www.vietnammm.com" + item.find('a', class_='restaurantname').get('href')
                if "https://www.vietnammm.com%7B%7Brestauranturl%7D%7D/" == url:
                    continue
                browser.get(url)

            # ---1111111111111111restaurant name,
            # ---1111111111111111restaurant address, (under “Info” tab)
            # ---1111111111111111delivery fee, (if exists)
            # ---111111111111111minimum order, (under “Info” tab)
            # ---1111111111111111delivery coverage, (under “Info” tab)
            # ---food name, (under “Menu” tab)
            # ---food price, (under “Menu” tab)
            # ---food category, (under “Menu” tab)
            # ---1111111111111111location (chosen location),
            # ---1111111111111111current date
            try:
                wait2.until(lambda browser: browser.find_element_by_xpath('/html/body/header/div[1]/div[7]/div/div[1]/h1/dt/span'))
            except TimeoutException:
                continue
            soup = BeautifulSoup(browser.page_source, 'lxml')

            if soup.find('span', class_='title-delivery') != None:
                restaurant_name = soup.find('span', class_='title-delivery').text.strip()
            else:
                restaurant_name = None

            href = browser.find_element_by_xpath('//*[@id="tab_MoreInfo"]/a').get_attribute('href')
            browser.get(href)

            wait.until(lambda browser: browser.find_element_by_xpath('/html/body/header/div[1]/div[7]/div/div[1]/h1/dt/span'))
            soup = BeautifulSoup(browser.page_source, 'lxml')

            restaurant_address = None
            if soup.find('span', itemprop='streetAddress') != None:
                restaurant_address = soup.find('span', itemprop='streetAddress').text.strip()
            if soup.find('span', itemprop='addressLocality') != None:
                if restaurant_address != None:
                    restaurant_address = restaurant_address + " "  + soup.find('span', itemprop='addressLocality').text.strip()
                else:
                    restaurant_address = soup.find('span', itemprop='addressLocality').text.strip()
            if "- - " in restaurant_address:
                restaurant_address = restaurant_address.replace('-','')
                restaurant_address = restaurant_address.strip()

            if item.find('div', class_='delivery').find('div', class_='delivery') != None:
                delivery_fee = item.find('div', class_='delivery').find('div', class_='delivery').text.strip()
            else:
                delivery_fee = None

            if item.find('div', class_='min-order') != None:
                minimum_order = item.find('div', class_='min-order').text.strip()
            else:
                minimum_order = None

            delivery_coverage = ""
            if soup.find('div', class_='moreinfo_deliveryareas') != None:
                if soup.find('div', class_='moreinfo_deliveryareas').find('ul') != None:
                    list = soup.find('div', class_='moreinfo_deliveryareas').find('ul').find_all('li')
                    for itam in list:
                        delivery_coverage = delivery_coverage + itam.text.strip() + "\n"
                else:
                    delivery_coverage = None
            else:
                delivery_coverage = None

            if delivery_coverage != None:
                delivery_coverage = delivery_coverage.strip()

            browser.get(url)
            try:
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="imenucard"]'))
            except TimeoutException:
                continue
            soup = BeautifulSoup(browser.page_source, 'lxml')

            main_list = soup.find('div', id='imenucard')
            if main_list is None:
                main_listm = []
            else:
                main_list = main_list.find_all('div', class_='menu-meals-group')
            for main_el in main_list:
                food_category = main_el.find('div', class_='menu-category-head').find('span').text.strip()
                list = main_el.find('div', class_='category-menu-meals').find_all('div', class_='meal')
                for el in list:
                    food_name = el.find('span', class_='meal-name').text.strip()
                    food_price = el.find('span', itemprop='price').text.strip()
                    data = {'location': location,
                            'restaurant_name': restaurant_name,
                            'restaurant_address': restaurant_address,
                            'delivery_fee': delivery_fee,
                            'minimum_order': minimum_order,
                            'delivery_coverage': delivery_coverage,
                            'food_category': food_category,
                            'food_name': food_name,
                            'food_price': food_price,
                            'date': DATE}
                    write_csv(data)
            # print(str(k+1) + "/" + str(len(glob_list)))
            k+=1
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
