import sys
import os
import glob
from zipfile import ZipFile
import time
import datetime
import schedule
import re
import csv
import random
import logging
from rich.logging import RichHandler
from rich.progress import track
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import signal


# Parameters
SITE_NAME = "tiki"
BASE_URL = "https://tiki.vn"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0

# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
# OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


# Setting up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")


# Defining main functions
def main():
    try:
        daily_task()
    except Exception as e:
        log.exception('Got exception, scraper stopped')
        log.info(type(e).__name__ + str(e))
    # Compress data and html files
    compress_csv()
    compress_html()
    log.info('Finished. Hibernating until next day...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    log.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Initiate headless web browser
    log.info('Initializing browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    # html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list()
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in track(CATEGORIES_PAGES,
                     description = "[green]Scraping...",
                     total = len(CATEGORIES_PAGES)):
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
    # Close browser
    BROWSER.close()
    BROWSER.service.process.send_signal(signal.SIGTERM)
    BROWSER.quit()


def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                BROWSER.get(url)
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
                with open(path + file_name, "w") as f:
                    f.write(html_content)
                log.debug(f"Downloaded: {file_name}")
                return(True)
            except:
                attempts += 1
                log.warning("Try again" + file_name)
        else:
            log.error(f"Cannot download {file_name}")
            return(False)
    else:
        log.debug(f"Already downloaded {file_name}")
        return(True)


def get_category_list():
    """Get list of relative categories directories from the top page"""
    global BROWSER
    page_list = []
    categories_tags = []
    tag = dict()
    nav_div = BROWSER.find_element_by_css_selector("ul[data-view-id='main_navigation']")
    cat1s = nav_div.find_elements_by_css_selector("li.MenuItem-sc-181aa19-0")
    for cat1 in cat1s:
        cat1_text = cat1.find_element_by_css_selector('a').text.strip()
        ActionChains(BROWSER).move_to_element(cat1).perform()
        cat2s = cat1.find_elements_by_css_selector('li')
        for cat2 in cat2s:
            link_tags = cat2.find_elements_by_css_selector('a')
            for elem in link_tags:
                cat2_text = elem.text.strip()
                tag['text'] = cat1_text + " > " + cat2_text
                tag['href'] = elem.get_attribute('href')
                categories_tags.append(tag.copy())
    # Unifying categories
    for cat in categories_tags:
        page = {}
        link = re.sub(r".+tiki\.vn", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.+", "_", link)
        page['label'] = re.sub("\\n", "", cat['text'])
        page_list.append(page)
    # Remove duplicates
    # page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    global OBSERVATION
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    cat_div = soup.findAll("a", {"class": "product-item"})
    for item in cat_div:
        row = {}
        good_name = item.find('div', {'class': 'name'})
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {'class': 'price-discount__price'})
        row['price'] = price.text.strip() if price else None
        discount = item.find('div', {"class": 'price-discount__discount'})
        row['discount'] = discount.text.strip() if discount else None
        row['id'] = item.get('href') if item else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
        OBSERVATION += 1
        write_data(row)


# def find_next_page(cat):
#     """Find the next page button, return page data"""
#     cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
#                     DATE + ".html").read()
#     cat_soup = BeautifulSoup(cat_file, "lxml")
#     next_button = cat_soup.find("div", {"class": "Pagination__Root-cyke21-0 imTRLy}")
#     if next_button:
#         link = re.sub(".+dichonhanh\.vn", "", cat['directlink'])
#         link = re.sub("\?page=[0-9]+", "", link)
#         link = link + next_button['href']
#         if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
#             next_page = cat.copy()
#             next_page['relativelink'] = link
#             next_page['directlink'] = BASE_URL + link
#             next_page['name'] = re.sub("/|\\?.=", "_", link)
#             CATEGORIES_PAGES.append(next_page)


def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', "id", 'price',
                  'discount', 'category', 'category_label', 'date']
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", "a") as f:
        writer = csv.DictWriter(f, fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(item_data)


def compress_csv():
    """Compress downloaded .csv files"""
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    os.chdir(PATH_CSV)
    try:
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a')
        for file in glob.glob("*" + DATE + "*" + "csv"):
            zip_csv.write(file)
            os.remove(file)
        log.info(f"Compressing {str(OBSERVATION)} item(s)")
    except Exception as e:
        log.error('Error when compressing csv')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)


def compress_html():
    """Compress downloaded .html files"""
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    os.chdir(PATH_HTML)
    try:
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_html.zip', 'a')
        for file in glob.glob("*" + DATE + "*" + "html"):
            zip_csv.write(file)
            os.remove(file)
        log.info("Compressing HTML files")
    except Exception as e:
        log.error('Error when compressing html')
        log.info(type(e).__name__ + str(e))
    os.chdir(PROJECT_PATH)


# Run scripts if argument is 'test', run and hibernate if 'run' else hibernate
if "test" in sys.argv:
    main()
else:
    if "run" in sys.argv:
        main()
    start_time = '01:' + str(random.randint(0, 59)).zfill(2)
    schedule.every().day.at(start_time).do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
