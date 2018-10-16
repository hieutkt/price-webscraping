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
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException


SITE_NAME = "now"
BASE_URL = "https://www.now.vn"
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
            writer.writerow(('category', 'food_category', 'location', 'seller', 'delivery_fee', 'food_type', 'food_name', 'food_orders', 'food_price', 'old_price', 'date'))
        writer.writerow((data['category'], data['food_category'], data['location'], data['seller'], data['delivery_fee'], data['food_type'], data['food_name'], data['food_orders'], data['food_price'], data['old_price'], data['date']))

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
    # chromeOptions.add_argument("--disable-javascript")
    chromeOptions.add_experimental_option("prefs",prefs)
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument("disable-infobars")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    browser2 = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(chrome_options=chromeOptions)
    browser2.set_window_position(100, 40)
    browser2.set_window_size(1300, 1024)
    wait2 = ui.WebDriverWait(browser2,30)
    # browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,30)
    browser.get(BASE_URL)
    urls = []
    titles = []
    wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[2]/nav/div/div[3]'))
    soup = BeautifulSoup(browser.page_source, 'lxml')
    category_list = soup.find('nav', class_='white').find('div', class_='top-cate').find_all('a')
    c=0
    for item in category_list:
        if c==0 :
            c+=1
            continue
        href = BASE_URL + item.get('href')
        title = item.text.strip()
        if href not in urls:
            urls.append(href)
            titles.append(title)
        c+=1
    # print(len(category_list))
    # print(category_list)
    # print(len(urls))
    # print(urls)
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])
        wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="list-page"]/div[2]/div[33]'))
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category = titles[j]

        i=0
        pagination = True
        while pagination:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="list-page"]/div[2]/div[33]'))
                    element = browser.find_element_by_css_selector('#list-page > div.container-list-restaurant.clearfix.active-view-column > div.pagation.clearfix > a.ico-page.ico-page-next.ng-scope')
                    if element.is_displayed():
                        browser.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                    else:
                        pagination = False
                    wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="list-page"]/div[2]/div[33]'))
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', id='list-page').find_all('div', class_='view-column-list')
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', id='list-page').find_all('div', class_='view-column-list')
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            for item in list:
                # if item.find('div', class_='ct_title') != None:
                #     title = item.find('div', class_='ct_title').text.strip()
                # else:
                #     title = None
                try:
                    href = BASE_URL + item.find('a').get('href')
                    browser2.get(href)
                    # wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="right"]/div[1]'))
                    soup = BeautifulSoup(browser2.page_source, 'lxml')
                except TimeoutException:
                    continue
                except:
                    continue

                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('h2', class_='kind-restaurant') != None:
                        food_category = soup.find('div', class_='info-basic-hot-restaurant').find('h2', class_='kind-restaurant').text.strip()
                        if soup.find('div', class_='info-basic-hot-restaurant').find('h2', class_='kind-restaurant').find('a') != None:
                            txt = soup.find('div', class_='info-basic-hot-restaurant').find('h2', class_='kind-restaurant').find('a').text.strip()
                            food_category = food_category.replace(txt, '')
                            food_category = food_category.strip()
                    else:
                        food_category = None
                except:
                    food_category = None

                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('h1', class_='name-hot-restaurant') != None:
                        seller = soup.find('div', class_='info-basic-hot-restaurant').find('h1', class_='name-hot-restaurant').text.strip()
                    else:
                        seller = None
                except:
                    seller = None

                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description') != None:
                        location = soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description').text.strip()
                    else:
                        location = None
                except:
                    location = None


                try:
                    if soup.find('div', class_='slick-list').find('span', class_='font14') != None:
                        delivery_fee = soup.find('div', class_='slick-list').find('span', class_='font14').text.strip()
                        delivery_fee = delivery_fee.replace('[?]','')
                    else:
                        delivery_fee = None
                except:
                    delivery_fee = None


                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description') != None:
                        location = soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description').text.strip()
                    else:
                        location = None
                except:
                    location = None


                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description') != None:
                        location = soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description').text.strip()
                    else:
                        location = None
                except:
                    location = None


                try:
                    if soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description') != None:
                        location = soup.find('div', class_='info-basic-hot-restaurant').find('p', itemprop='description').text.strip()
                    else:
                        location = None
                except:
                    location = None


                # 555555555555555---location,
                # 555555555555555---seller,
                # 555555555555555---delivery fee,
                # ---food name,
                # ---food price,
                # ---food old_price (previous price if exists),
                # ---food orders,
                # 111111---food type,
                # 55555555555---food category,
                # 55555555555---category (name of category),
                # 55555555555---current date
                try:
                    products_types = soup.find('div', class_='detail-menu-kind').find_all('div', class_='scrollspy')
                except:
                    continue
                # print(products_types)
                for products_type in products_types:
                    # print(products_type)
                    food_type = products_type.find('h2', class_='title-kind-food').text.strip()
                    products = products_type.find_all('div', class_='box-menu-detail')
                    for product in products:
                        try:
                            food_name = product.find('h3').text.strip()
                        except:
                            continue
                        try:
                            food_orders = product.find('div', class_='name-food-detail').find('p', class_='light-grey').text.strip()
                        except:
                            continue
                        try:
                            food_price = product.find('div', class_='product-price').find('p', class_='current-price').text.strip()
                        except:
                            continue
                        try:
                            old_price = product.find('div', class_='product-price').find('p', class_='old-price').text.strip()
                        except:
                            old_price = None
                        data = {'category': category,
                                'food_category': food_category,
                                'location': location,
                                'seller': seller,
                                'delivery_fee': delivery_fee,
                                'food_type': food_type,
                                'food_name': food_name,
                                'food_orders': food_orders,
                                'food_price': food_price,
                                'old_price': old_price,
                                'date': DATE}
                        write_csv(data)
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
