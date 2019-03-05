import sys
import os
import time
import datetime
import schedule
import re
import csv
import random
import coloredlogs, logging
import logging.handlers as handlers
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


# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


# Setting up logging
log_format = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p'
)
log_writer = logging.FileHandler(PATH_LOG + SITE_NAME + '.log')
log_stout = logging.StreamHandler()
log_error = handlers.TimedRotatingFileHandler(PATH_LOG + 'aggregated_error/errors.log',
    when = 'midnight', interval=1)
log_error.suffix = '%Y-%m-%d_' + SITE_NAME

log_writer.setFormatter(log_format)
log_stout.setFormatter(log_format)
log_error.setFormatter(log_format)
log_error.setLevel("ERROR")

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[log_writer, log_stout, log_error]
)

coloredlogs.install()


# Defining main functions
def main():
    try:
        daily_task()
    except Exception as e:
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_data()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE

    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    # Initiate headless web browser
    logging.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, BROWSER)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.warning("Try again" + file_name)
        else:
            logging.error("Cannot download" + file_name)
            return(False)
    else:
        logging.debug("Already downloaded " + file_name)
        return(True)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.findAll("ul", attrs={'id': 'nav'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        next_page = {}
        link = re.sub(".+cellphones\.com\.vn", "", cat['href'])
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
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    cat_div = soup.find("div", {"class": "products-container"})
    if cat_div is not None:
        cat_ul = cat_div.find("ul")
        if cat_ul:
            cat_li = cat_ul.findAll("li", recursive=False)
        else: cat_li = []
    else:
        cat_li = []
    data = []
    for item in cat_li:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.contents[0] if good_name else None
        price_tag = item.find('p', {'class': 'special-price'})
        if not price_tag:
            price_tag = item.find('span', {'class': 'regular-price'})
        price = price_tag.find('span', {'class': 'price'})\
            if price_tag else None
        row['price'] = price.contents[0] if price else None
        old_price_tag = item.find('p', {'class': 'old-price'})
        old_price = old_price_tag.find('span', {'class': 'price'})\
            if old_price_tag else None
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.find('a')
        row['id'] = id1.get('href') if id1 else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
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


def compress_data():
    """Compress downloaded .csv and .html files"""
    zip_csv = "cd " + PATH_CSV + "&& tar -czf " + SITE_NAME + "_" + \
        DATE + ".tar.gz *" + SITE_NAME + "_" + DATE + "* --remove-files"
    zip_html = "cd " + PATH_HTML + "&& tar -czf " + SITE_NAME + "_" + \
        DATE + ".tar.gz *" + DATE + ".html* --remove-files"
    logging.info('Compressing files')
    try:
        os.system(zip_csv)
        os.system(zip_html)
    except Exception as e:
        logging.error('Error when compressing data')
        logging.info(e)


if "test" in sys.argv:
    main()
else:
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
