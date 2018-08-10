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
from selenium.webdriver.support.ui import Select
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options



SITE_NAME = "caganu"
BASE_URL = "https://caganu.com"
PROJECT_PATH = re.sub("/py/upworks$", "", os.getcwd())
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
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, delimiter=',')
        writer.writerow(data)

def write_html(html, file_name):
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
    # browser.find_element_by_xpath('//*[@id="province-change"]').click()
    wait.until(lambda browser: browser.find_element_by_css_selector('#Modal-choiceProvince > div > div > div'))
    select = Select(browser.find_element_by_xpath('//*[@id="txtProvince"]'))
    select.select_by_value('62') # Hanoi
    location = "Hà Nội"
    browser.find_element_by_xpath('//*[@id="confirmChoiceProvince"]').click()
    urls = []
    titles = []
    main_category_list = soup.find('div', id='for-home').find_all('div', class_='menu_list')
    for item in main_category_list:
        href = BASE_URL + item.find('a').get('href')
        title = item.find('div', class_='menu_title').text.strip()
        urls.append(href)
        titles.append(title)
    j=0
    write_html(browser.page_source, "All_cat_")
    while j < len(urls):
        browser.get(urls[j])
        category = titles[j]

        # print(page_count)
        i=0
        soup = BeautifulSoup(browser.page_source, 'lxml')
        pagination = soup.find('ul', class_='pagination').find_all('li')
        pagination = pagination[len(pagination)-1]
        pagination = pagination.find('a').get('href')
        pagination = pagination.split('page=')[1]
        pagination = pagination.split('&')[0]
        while i < int(pagination):
            if i != 0:
                elements = browser.find_elements_by_css_selector('ul.pagination > li')
                c=0
                while c < len(elements):
                    try:
                        element = elements[c].find_element_by_css_selector('a.select-pagi')
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
                wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="CategoryContent"]/div/div/div[2]/div[4]/div/div/nav/ul'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='category-list-product-item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='category-list-product-item')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = BASE_URL + item.find('a').get('href').strip()
                # item_id = item_id.split('-')
                # item_id = item_id[len(item_id)-1]
                # print(item_id)
                # time.sleep(1200)
                # Vietnamese
                # English
                if item.find('h3', class_='product-info-title') != None:
                    title_Vietnamese = item.find('h3', class_='product-info-title').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('span', class_='product-info-price-sale') != None:
                    price = item.find('span', class_='product-info-price-sale').text.strip()
                    # price = price.split('₫')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='product-info-original') != None:
                    old_price = item.find('span', class_='product-info-original').text.strip()
                    # old_price = old_price.split('₫')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'id': item_id,
                        'title_Vietnamese': title_Vietnamese,
                        'location': location,
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
