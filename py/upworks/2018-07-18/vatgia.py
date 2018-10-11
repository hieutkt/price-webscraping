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
from selenium.webdriver.common.action_chains import ActionChains

SITE_NAME = "vatgia"
BASE_URL = "https://www.vatgia.com"
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
            writer.writerow(('category', 'sub_category', 'id', 'title_Vietnamese', 'location', 'price', 'old_price', 'old_price', 'date'))
        writer.writerow((data['category'], data['sub_category'], data['id'], data['title_Vietnamese'], data['location'], data['price'], data['old_price'], data['old_price'], data['date']))

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
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    browser.get('https://www.vatgia.com/home/')
    # loadAjaxContent('/ajax_v5/load_menu.php', 'ajax_v5_load_menu');
    # browser.execute_script('/ajax_v5/load_menu.php', 'ajax_v5_load_menu')
    element_to_hover_over = browser.find_element_by_xpath('//*[@id="header_navigate"]/div[1]')
    hover = ActionChains(browser).move_to_element(element_to_hover_over)
    hover.perform()
    time.sleep(1)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    urls = []
    main_category_list = soup.find('ul', id='menu_home_navigate').find_all('div', class_='root')
    write_html(browser.page_source, "All_cat_")
    for main_item in main_category_list:
        if main_item.find('a') != None:
            url = main_item.find('a').get('href')
            if "vatgia.com" not in url:
                url = BASE_URL + main_item.find('a').get('href')
            urls.append(url)
    # print(len(main_category_list))
    # print(len(urls))
    # print(urls)
    # time.sleep(1200)
# cat-tree-nav
    j=0
    while j < len(urls):
        print('Scraping', urls[j])
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category_titles = soup.find('div', id='header_navigate_breadcrumb')
        if category_titles is not None:
            category_titles = category_titles.find_all('a')

        if len(category_titles) == 2:
            category = category_titles[1].text.strip()
            sub_category = None
        if len(category_titles) == 3:
            category = category_titles[1].text.strip()
            sub_category = category_titles[2].text.strip()
        if len(category_titles) == 4:
            category = category_titles[1].text.strip()
            sub_category = category_titles[2].text.strip()

        # print(page_count)
        try:
            i=0
            page_count = soup.find('div', class_='page_bar').find('a', class_='last').get('href')
            page_count = page_count.split(',')
            page_count = page_count[len(page_count)-1]
            page_count = page_count.strip()
        except:
            j+=1
            continue
        while i < int(page_count):
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                browser.get(urls[j] + "," + str(i+1))
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', id='type_product_up').find_all('div', class_='wrapper')
                except:
                    i+=1
                    continue
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', id='type_product_up')
                    if list is None:
                        list = []
                    else:
                        list = list.find_all('div', class_='wrapper')
                except:
                    i+=1
                    continue
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.has_attr('idata'):
                    item_id = item.get('idata').strip()
                else:
                    continue
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('div', class_='estore') != None:
                    location = soup.select('div.estore > span.note_city')
                    if len(location) >= 2:
                        location = soup.select('div.estore > span.note_city')[1]
                        location = location.text.strip()
                    else:
                        location = None
                else:
                    location = None

                if item.find('div', class_='name') != None:
                    title_Vietnamese = item.find('div', class_='name').text.strip()
                else:
                    title_Vietnamese = None
                # if item.find('div', class_='english_name') != None:
                #     title_English = item.find('div', class_='english_name').text.strip()
                # else:
                #     title_English = None
                # print("Title: " + title)
                if item.find('div', class_='price') != None:
                    price = item.find('div', class_='price').text.strip()
                    # price = price.split('đ')[0]
                    # price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='old_price') != None:
                    old_price = item.find('span', class_='old_price').text.strip()
                    # old_price = old_price.split('đ')[0]
                    # old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'sub_category': sub_category,
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

if __name__ == '__main__':
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
