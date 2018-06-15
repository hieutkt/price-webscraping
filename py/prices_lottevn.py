import sys
import os
import time
import datetime
import schedule
import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Parameters
SITE_NAME = "lottevn"
BASE_URL = "https://www.lotte.vn/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    global CATEGORIES_PAGES
    global BROWSER
    # Initiate headless web browser
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Refresh date
    DATE = str(datetime.date.today())
    # Download topsite and get categories directories
    CATEGORIES_PAGES = get_category_list(BASE_URL)
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            find_next_page(cat)
    # Close browser
    BROWSER.close()
    # Compress data and html files
    compress_data()


def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                BROWSER.get(url)
                grid = False
                while grid is False:
                    try:
                        grid = BROWSER.find_element_by_css_selector('.item-product')
                    except Exception:
                        time.sleep(0.5)
                        grid += 1
                        pass
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
                with open(path + file_name, "w") as f:
                    f.write(html_content)
                print("Downloaded ", file_name)
                return(True)
            except Exception:
                attempts += 1
                print("Try again", file_name)
        else:
            print("Cannot download", file_name)
            return(False)
    else:
        print("Already downloaded ", file_name)
        return(True)


def get_category_list(url):
    """Get list of relative categories directories from the top page"""
    base_file_name = "All_cat_" + DATE + ".html"
    BROWSER.get(url)
    menu_not_shown = True
    while menu_not_shown:
        try:
            dropdown = BROWSER.find_element_by_css_selector('.megamenu')
            dropdown.click()
            menu_not_shown = False
        except Exception:
            pass
    menu_content = dropdown.get_attribute('innerHTML')
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + base_file_name, "w") as f:
        f.write(menu_content)
    print("Downloaded ", base_file_name)
    toppage_soup = BeautifulSoup(menu_content, "lxml")
    categories = toppage_soup.findAll("a")
    page_list = []
    for cat in categories:
        next_page = {}
        link = re.sub(".+lotte\.vn", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        next_page['label'] = re.sub("\\n", "", cat.text)
        page_list.append(next_page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_div = cat_soup.findAll("div", {"class": "item-product"})
    if cat_div is None:
        print("Nothing found on" + cat['label'])
    for item in cat_div:
        row = {}
        good_name = item.find('p', {"class": "product-name"})
        if good_name:
            row['good_name'] = re.sub("\n", "", good_name.text)
        price = item.find('span', {"class": "current-price"})
        if price:
            row['price'] = re.sub("\n| ", "", price.text)
        old_price = item.find('p', {"class": "old-price"})
        if old_price:
            row['old_price'] = re.sub("\n| ", "", old_price.text)
        id1 = item.find("a")
        row['id'] = id1.get("href") if id1 else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
        write_data(row)


def find_next_page(cat):
    """Find the next page button and return the next page info"""
    current_url = BROWSER.current_url
    try:
        next_button = BROWSER.find_element_by_class_name("pages-item-next")
    except Exception:
        next_button = None
    if next_button is not None:
        try:
            next_button.click()
        except Exception:
            pass
        link = BROWSER.current_url
        if link != current_url:
            if link not in [i['directlink'] for i in CATEGORIES_PAGES]:
                next_page = cat.copy()
                link = re.sub(".+lotte\.vn", "", link)
                next_page['relativelink'] = link
                next_page['directlink'] = BASE_URL + link
                next_page['name'] = re.sub("/|\\?.=", "_", link)
                CATEGORIES_PAGES.append(next_page)


def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id',
                  'category', 'category_label', 'date']
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", "a") as f:
        writer = csv.DictWriter(f, fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(item_data)


def compress_data():
    """Compress downloaded .csv and .html files"""
    zip_csv = "cd " + PATH_CSV + "&& tar -cvzf " + SITE_NAME + "_" + \
        DATE + ".tar.gz *" + SITE_NAME + "_" + DATE + "* --remove-files"
    zip_html = "cd " + PATH_HTML + "&& tar -cvzf " + SITE_NAME + "_" + \
        DATE + ".tar.gz *" + DATE + ".html* --remove-files"
    os.system(zip_csv)
    os.system(zip_html)


if "test" in sys.argv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)
