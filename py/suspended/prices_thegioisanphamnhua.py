import sys
import os, glob
from zipfile import ZipFile
import time
import datetime
import schedule
import re
import csv
import random
import coloredlogs, logging
import logging.handlers as handlers
from urllib.request import urlopen
from bs4 import BeautifulSoup


# Parameters
SITE_NAME = "thegioisanphamnhua"
BASE_URL = "http://thegioisanphamnhua.com/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0


# Setting up logging
if not os.path.exists(PATH_LOG):
    os.makedirs(PATH_LOG)
    os.makedirs(PATH_LOG + "/aggregated_error/")
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
        log.exception('Got exception, scraper stopped')
        log.info(type(e).__name__ + str(e))
    # Compress data and html files
    compress_csv()
    compress_html()
    log.info('Finished. Hibernating until next day...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    log.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            find_next_page(cat)


def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                con = urlopen(url, timeout=5)
                html_content = con.read()
                with open(path + file_name, "wb") as f:
                    f.write(html_content)
                    con.close
                log.debug("Downloaded: %s", file_name)
                return(True)
            except:
                attempts += 1
                log.debug("Downloaded: %s", file_name)
        else:
            log.error("Cannot download " + file_name)
            return(False)
    else:
        log.debug("Already downloaded %s", file_name)
        return(True)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.find('ul', {'id': 'nav-top'})
    categories = categories.findAll('li')
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+thegioisanphamnhua\.com/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.=", "_", link)
        page['label'] = cat.text
        page_list.append(page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global OBSERVATION
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_div = cat_soup.findAll("div", {"class": "row_pro_cat"})
    for item in cat_div:
        row = {}
        price = item.find('div', {"style": re.compile('#ff3200')})
        row['price'] = price.contents[0].strip() if price else None
        old_price = price.find('span', {"style": re.compile('#4c4444')}) if price else None
        row['old_price'] = old_price.text.strip() if old_price else None
        good_name = price.findNext('a') if price else None
        row['good_name'] = good_name.text.strip() if good_name else None
        row['id'] = good_name.get('href') if good_name else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
        OBSERVATION += 1
        write_data(row)


def find_next_page(cat):
    """Find the next page button, return page data"""
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    next_button = cat_soup.find('a', {'title': 'Tiếp theo'})
    if next_button:
        link = re.sub(".+123wow\.vn", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
            next_page['relativelink'] = link
            next_page['directlink'] = BASE_URL + link
            next_page['name'] = cat['name']
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
