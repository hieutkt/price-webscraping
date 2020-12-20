import sys
import os, glob
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
import signal


# Parameters
SITE_NAME = "cellphones"
BASE_URL = "https://cellphones.com.vn/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0


# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
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
    log.info('Hibernating...')


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
    log.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, BROWSER)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in track(CATEGORIES_PAGES,
                     description = "[green]Scraping...",
                     total = len(CATEGORIES_PAGES)):
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML, BROWSER)
        if download:
            scrap_data(cat)
    # Close browser
    BROWSER.close()
    BROWSER.service.process.send_signal(signal.SIGTERM)
    BROWSER.quit()


def fetch_html(url, file_name, path, browser):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < 5:
            try:
                browser.get(url)
                html_content = browser.page_source
                with open(path + file_name, "w") as f:
                    f.write(html_content)
                log.debug("Downloaded: %s", file_name)
                return(True)
            except:
                attempts += 1
                log.warning("Try again" + file_name)
        else:
            log.error("Cannot download %s", file_name)
            return(False)
    else:
        log.debug("Already downloaded %s", file_name)
        return(True)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.findAll("ul", {'class': 'col-md-12'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    # Remove duplicate links
    cat_check = []
    for c in categories_tag:
        if c.get('href') \
           and c.get('href') not in [c.get('href') for c in cat_check]:
            cat_check.append(c)
    # Get infomation from category tags
    for cat in cat_check:
        next_page = {}
        link = re.sub(r".+cellphones\.com\.vn", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        next_page['label'] = re.sub("\\n", "", cat.text.strip())
        page_list.append(next_page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    global OBSERVATION
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    cat_div = soup.find("div", {"class": "products-container"})
    if cat_div is not None:
        cat_ul = cat_div.find("ul")
        if cat_ul:
            cat_li = cat_ul.findAll("li", recursive=False)
        else: cat_li = []
    else:
        cat_li = []
    for item in cat_li:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price_tag = item.find('p', {'class': 'special-price'})
        if not price_tag:
            price_tag = item.find('span', {'class': 'regular-price'})
        price = price_tag.find('span', {'class': 'price'})\
            if price_tag else None
        row['price'] = price.text.strip() if price else None
        old_price_tag = item.find('p', {'class': 'old-price'})
        old_price = old_price_tag.find('span', {'class': 'price'})\
            if old_price_tag else None
        row['old_price'] = old_price.text.strip() if old_price else None
        id1 = item.find('a')
        row['id'] = id1.get('href') if id1 else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
        OBSERVATION += 1
        write_data(row)


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


def compress_csv():
    """Compress downloaded .csv files"""
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    os.chdir(PATH_CSV)
    try:
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a') #
        for file in glob.glob("*" + DATE + "*" + "csv"):
            zip_csv.write(file)
            os.remove(file)
        log.info("Compressing %s item(s)", str(OBSERVATION))
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
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_html.zip', 'a') #
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
