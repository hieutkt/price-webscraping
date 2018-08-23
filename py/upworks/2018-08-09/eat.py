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



SITE_NAME = "eat"
BASE_URL = "https://eat.vn/"
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
            writer.writerow(('location', 'restaurant_name', 'restaurant_address', 'minimum_order', 'food_category', 'food_name', 'food_price', 'date'))
        writer.writerow((data['location'], data['restaurant_name'], data['restaurant_address'], data['minimum_order'], data['food_category'], data['food_name'], data['food_price'], data['date']))


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
    browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    browser.get(BASE_URL)
    urls = []
    # urls = ['https://eat.vn/restaurants/District-Huyen-Binh-Chanh-60.html', 'https://eat.vn/restaurants/District-1-8.html', 'https://eat.vn/restaurants/District-2-9.html', 'https://eat.vn/restaurants/District-3-10.html', 'https://eat.vn/restaurants/District-4-11.html', 'https://eat.vn/restaurants/District-5-12.html', 'https://eat.vn/restaurants/District-6-32.html', 'https://eat.vn/restaurants/District-7-13.html', 'https://eat.vn/restaurants/District-8-14.html', 'https://eat.vn/restaurants/District-9-15.html', 'https://eat.vn/restaurants/District-10-16.html', 'https://eat.vn/restaurants/District-11-17.html', 'https://eat.vn/restaurants/District-12-18.html', 'https://eat.vn/restaurants/District-Binh-Tan-2.html', 'https://eat.vn/restaurants/District-Binh-Thanh-5.html', 'https://eat.vn/restaurants/District-Go-Vap-6.html', 'https://eat.vn/restaurants/District-Phu-Nhuan-7.html', 'https://eat.vn/restaurants/District-Tan-Binh-19.html', 'https://eat.vn/restaurants/District-Thu-Duc-21.html', 'https://eat.vn/restaurants/District-Tan-Phu-20.html', 'https://eat.vn/restaurants/District-An-Phu-33.html', 'https://eat.vn/restaurants/District-Phu-My-Hung-34.html', 'https://eat.vn/restaurants/District-City-Garden-Binh-Thanh-57.html', 'https://eat.vn/restaurants/District-Saigon-Pearl-Binh-Thanh-54.html', 'https://eat.vn/restaurants/District-The-Manor-Binh-Thanh-51.html', 'https://eat.vn/restaurants/District-Cu-Chi-42.html', 'https://eat.vn/restaurants/District-Hoc-Mon-40.html', 'https://eat.vn/restaurants/District-Nha-Be-39.html', 'https://eat.vn/restaurants/District-Tay-Ho-30.html', 'https://eat.vn/restaurants/District-Ciputra-Tay-Ho-59.html', 'https://eat.vn/restaurants/District-Ba-Dinh-3.html', 'https://eat.vn/restaurants/District-Hoan-Kiem-25.html', 'https://eat.vn/restaurants/District-Dong-Da-22.html', 'https://eat.vn/restaurants/District-Cau-Giay-4.html', 'https://eat.vn/restaurants/District-Hai-Ba-Trung-24.html', 'https://eat.vn/restaurants/District-Thanh-Xuan-31.html', 'https://eat.vn/restaurants/District-Hoang-Mai-26.html', 'https://eat.vn/restaurants/District-Ha-Dong-23.html', 'https://eat.vn/restaurants/District-Long-Bien-27.html', 'https://eat.vn/restaurants/District-Bac-Tu-Liem-45.html', 'https://eat.vn/restaurants/District-Gia-Lam-37.html', 'https://eat.vn/restaurants/District-Nam-Tu-Liem-44.html', 'https://eat.vn/restaurants/District-Tu-Liem-38.html', 'https://eat.vn/restaurants/District-My-Dinh-43.html', 'https://eat.vn/restaurants/District-My-Duc-29.html']
    titles = []
    write_html(browser.page_source, "All_cat_")
    elem = browser.find_element_by_css_selector('#province_chosen > a')
    # browser.execute_script("arguments[0].click();", elem)
    elem.click()
    wait.until(lambda browser: browser.find_elements_by_css_selector('#province_chosen > div > ul.chosen-results > li'))
    elements = browser.find_elements_by_css_selector('#province_chosen > div > ul.chosen-results > li')
    # print(len(elements))
    c=0
    while c < len(elements):
        if c > 0:
            elem = browser.find_element_by_css_selector('#province_chosen > a')
            # browser.execute_script("arguments[0].click();", elem)
            elem.click()
        try:
            wait2.until(lambda browser: browser.find_elements_by_css_selector('#province_chosen > div > ul.chosen-results > li'))
        except TimeoutException:
            elem.click()
            wait.until(lambda browser: browser.find_elements_by_css_selector('#province_chosen > div > ul.chosen-results > li'))
        elements = browser.find_elements_by_css_selector('#province_chosen > div > ul.chosen-results > li')
        # browser.execute_script("arguments[0].click();", elements[c])
        elements[c].click()
        if c > 0:
            time.sleep(5)
        wait.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > a'))
        elem2 = browser.find_element_by_css_selector('#district_chosen > a')
        # # browser.execute_script("arguments[0].click();", elem2)
        elem2.click()
        # time.sleep(5)
        wait.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li'))
        elements2 = browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li')
        texts = browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li')
        l=0
        for el in texts:
            # if l == 0:
            #     l+=1
            #     continue
            txt = el.text.strip()
            titles.append(txt)
            l+=1
        j=0
        while j < len(elements2):
            if j > 0:
                elem2 = browser.find_element_by_css_selector('#district_chosen > a')
                # browser.execute_script("arguments[0].click();", elem2)
                elem2.click()
                # elem2.click()
            try:
                wait2.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li'))
            except TimeoutException:
                elem2.click()
                wait.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li'))
            except StaleElementReferenceException:
                elem2.click()
                wait.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li'))
            wait.until(lambda browser: browser.find_element_by_css_selector('#district_chosen > div > div > input[type="text"]'))
            browser.find_element_by_css_selector('#district_chosen > div > div > input[type="text"]').send_keys(titles[j]+'\n')
            #district_chosen > div > div > input[type="text"]
            # wait.until(lambda browser: browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li'))
            # elements2 = browser.find_elements_by_css_selector('#district_chosen > div > ul.chosen-results > li')
            # # browser.execute_script("arguments[0].click();", elements2[j])
            # elements2[j].click()
            # time.sleep(5)
            wait.until(lambda browser: browser.find_elements_by_css_selector('a.find-btn'))
            old_url = browser.current_url
            elem = browser.find_element_by_css_selector('a.find-btn')
            # browser.execute_script("arguments[0].click();", elem)
            elem.click()
            new_url = browser.current_url
            k = 0
            while old_url == new_url:
                time.sleep(1)
                new_url = browser.current_url
                # browser.execute_script("arguments[0].click();", elem)
                if k >= 10:
                    elem = browser.find_element_by_css_selector('a.find-btn')
                    if elem.is_displayed():
                        # browser.execute_script("arguments[0].click();", elem)
                        elem.click()
                        k=0
                k+=1
            url = browser.current_url
            if url not in urls:
                urls.append(url)
            wait.until(lambda browser: browser.find_element_by_css_selector('a.change-location-btn'))
            elem3 = browser.find_element_by_css_selector('a.change-location-btn')
            element = browser.find_element_by_css_selector('body > main > div > div.search-title > div.choice-location.pop-up-lg')
            while not(element.is_displayed()):
                time.sleep(1)
                if not(elem3.is_displayed()):
                    break
                else:
                    elem3.click()
                time.sleep(2)
            # browser.execute_script("arguments[0].click();", elem)
            # browser.get(BASE_URL)
            j+=1
        titles[:] = []
        c+=1
    # print(len(urls))
    # print(urls)
    j=0
    while j < len(urls):
        browser.get(urls[j])


        soup = BeautifulSoup(browser.page_source, 'lxml')
        glob_list = soup.find('div', class_='list-restaurants').find_all('div', class_='item')

        i=0
        k=0
        file_name = str(j+1) + "_" + str(i+1) + "_"
        write_html(browser.page_source, file_name)
        for item in glob_list:
            # item = element.get_attribute('innerHTML')
            # item = BeautifulSoup(item, 'lxml')
            # print(item)
            if item.find('div', class_='action') == None:
                continue
            elif item.find('div', class_='action').find('a') == None:
                continue
            else:
                url = "https://eat.vn/" + item.find('div', class_='action').find('a').get('data-link')
                browser.get(url)

            # ---11111111111111111restaurant name,
            # ---1111111111111111111111restaurant address, (under “Restaurants info” tab)
            # ---delivery fee,
            # ---11111111111111111minimum order, (under “Restaurants info” tab)
            # ---delivery coverage,
            # ---food name, (under “Menu” tab)
            # ---food price, (under “Menu” tab)
            # ---food category, (under “Menu” tab)
            # ---111111111111111111111location (chosen location),
            # ---111111111111111111111current date

            soup = BeautifulSoup(browser.page_source, 'lxml')
            category_titles = soup.find('ol', class_='breadcrumb').find_all('li')
            if len(category_titles) >= 3:
                location = category_titles[2].find('a').text.strip()

            soup = BeautifulSoup(browser.page_source, 'lxml')

            if soup.find('div', class_='title') != None:
                if soup.find('div', class_='title').find('h2') != None:
                    restaurant_name = soup.find('div', class_='title').find('h2').text.strip()
                else:
                    restaurant_name = None
            else:
                restaurant_name = None

            elem = browser.find_element_by_xpath('//*[@id="tprofile"]')
            browser.execute_script("arguments[0].click();", elem)

            wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="profile"]/div[2]'))
            soup = BeautifulSoup(browser.page_source, 'lxml')

            restaurant_address = None
            if soup.find('div', class_='res-overview-detail') != None:
                if soup.find('div', class_='res-overview-detail').find('dd') != None:
                    restaurant_address = soup.find('div', class_='res-overview-detail').find('dd').text.strip()
                else:
                    restaurant_address = None
            else:
                restaurant_address = None

            restaurant_address = browser.find_element_by_css_selector('#profile > div.col-md-3.col-sm-4 > dl > dd:nth-child(2)').text.strip()

            minimum_order = browser.find_element_by_css_selector('#profile > div.col-md-3.col-sm-4 > dl > dd:nth-child(6)').text.strip()

            elem = browser.find_element_by_xpath('//*[@id="tfood-menu"]')
            browser.execute_script("arguments[0].click();", elem)

            wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="food-menu"]/div[2]/div[1]'))
            soup = BeautifulSoup(browser.page_source, 'lxml')


            main_list = soup.find('div', id='food-menu').find_all('div', class_='menu-item')
            for main_el in main_list:
                food_category = main_el.find('h3').text.strip()
                list = main_el.find('ul', class_='list-menu').find_all('li')
                for el in list:
                    food_name = el.find('h4').text.strip()
                    food_price = el.find('span', class_='price').text.strip()
                    data = {'location': location,
                            'restaurant_name': restaurant_name,
                            'restaurant_address': restaurant_address,
                            # 'delivery_fee': delivery_fee,
                            'minimum_order': minimum_order,
                            # 'delivery_coverage': delivery_coverage,
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
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
