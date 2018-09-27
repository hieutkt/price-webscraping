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

SITE_NAME = "hasaki"
BASE_URL = "https://www.hasaki.vn/"
PROJECT_PATH = os.getcwd()
PROJECT_PATH = PROJECT_PATH.replace("\\",'/')
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CHROME_DRIVER_PATH = "bin/chromedriver"
DATE = str(datetime.date.today())


def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'sub_category', 'sub_sub_category', 'id', 'title_Vietnamese', 'title_English', 'price', 'old_price', 'date'))
        writer.writerow((data['category'],data['sub_category'],data['sub_sub_category'],data['id'], data['title_Vietnamese'], data['title_English'], data['price'], data['old_price'], data['date']))

def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    chromeOptions.add_argument("--headless")
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    browser.get("https://www.hasaki.vn/")
    soup = BeautifulSoup(browser.page_source, 'lxml')
    # /html/body/div/div[2]
    waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
    while "Thank you" in waits:
        time.sleep(1)
        browser.refresh()
        waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
    soup = BeautifulSoup(browser.page_source, 'lxml')
    urls = []
    main_category_list = soup.find('div', class_='col_menu_cap1').find_all('a', class_='parent_menu')
    for item in main_category_list:
        href = "https://hasaki.vn/" + item.get('href')
        if "?" not in href:
            urls.append(href)
    main_category_list = soup.find('div', class_='col_menu_cap1').find_all('div', class_='col_hover_submenu')
    for main_item in main_category_list:
        category_list = main_item.find_all('a')
        for item in category_list:
            href = "https://hasaki.vn/" + item.get('href')
            if "?" not in href:
                urls.append(href)
    j=0
    write_html(browser.page_source, "All_cat_")
    while j < len(urls):
        browser.get(urls[j])
        waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
        while "Thank you" in waits:
            time.sleep(1)
            browser.refresh()
            waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
        soup = BeautifulSoup(browser.page_source, 'lxml')
        # if browser.find_element_by_xpath('//*[@id="lb_thongbao_canhtranh"]').is_displayed():
        #     element = browser.find_element_by_xpath('//*[@id="lb_thongbao_canhtranh"]/div[1]/button')
        #     browser.execute_script("arguments[0].click();", element)
        product_is = soup.find('div', class_='empty')
        if product_is != None:
            j+=1
            continue
        category_titles = soup.find('nav', id='breadcrumb').find_all('li')
        if len(category_titles) == 2:
            category = category_titles[1].find('a').text.strip()
            sub_category = None
            sub_sub_category = None
        if len(category_titles) == 3:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()
            sub_sub_category = None
        if len(category_titles) == 4:
            category = category_titles[1].find('a').text.strip()
            sub_category = category_titles[2].find('a').text.strip()
            sub_sub_category = category_titles[3].find('a').text.strip()

        # print(page_count)
        i=0
        is_next_elem = True
        while is_next_elem:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if soup.find('ul', class_='pagination') != None:
                page_count = soup.find('ul', class_='pagination').find_all('li')
            if i != 0:
                local_url = browser.find_element_by_xpath('//*[@id="col_right"]/nav/ul/li[' + str(len(page_count)) + ']/a')
                # //*[@id="col_right"]/nav/ul/li[6]/a
                local_url = local_url.get_attribute('href')
                # print(local_url)
                browser.get(str(local_url))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
                while "Thank you" in waits:
                    time.sleep(1)
                    browser.refresh()
                    waits = browser.find_element_by_xpath('/html/body/div/div[2]').text
                # wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="col_right"]/nav'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='product_item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find_all('div', class_='product_item')
            # print(len(list))
            # print(i+1)
            for item in list:
                item_id = item.find('a').get('href').strip()
                # item_id = item_id.split('id=')[1]
                # Vietnamese
                # English
                if item.find('div', class_='vietnam_name') != None:
                    title_Vietnamese = item.find('div', class_='vietnam_name').text.strip()
                else:
                    title_Vietnamese = None
                if item.find('div', class_='english_name') != None:
                    title_English = item.find('div', class_='english_name').text.strip()
                else:
                    title_English = None
                # print("Title: " + title)
                if item.find('span', class_='giamoi') != None:
                    price = item.find('span', class_='giamoi').text.strip()
                    price = price.split('₫')[0]
                    price = price.strip()
                else:
                    price = None
                # print("Price: " + str(price))
                if item.find('span', class_='giacu') != None:
                    old_price = item.find('span', class_='giacu').text.strip()
                    # old_price = old_price.split('₫')[0]
                    old_price = old_price.strip()
                else:
                    old_price = None
                
                date = DATE

                data = {'category': category,
                        'sub_category': sub_category,
                        'sub_sub_category': sub_sub_category,
                        'id': item_id,
                        'title_Vietnamese': title_Vietnamese,
                        'title_English': title_English,
                        'price': price,
                        'old_price': old_price,
                        'date': date}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if soup.find('ul', class_='pagination') != None:
                page_count = soup.find('ul', class_='pagination').find_all('li')
            for item in page_count:
                if item.find('a') != None:
                    next_elem = item.find('a').get('aria-label')
                    if next_elem == "Next":
                        is_next_elem = True
                        break
                    else:
                        is_next_elem = False
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
