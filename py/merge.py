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
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import signal
from pprint import pprint as pp

##### 123wow #######

# Parameters
SITE_NAME = "123wow"
BASE_URL = "https://123wow.vn/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.debug("Downloaded " + file_name)
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
    categories = toppage_soup.find('ul', {'id': 'sample-menu-1'})
    categories = categories.findAll('li')
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+123wow\.vn/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link + '?limit=100'
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
    cat_div = cat_soup.findAll("div", {"class": "product-inner clearfix"})
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('div', {"class": "name"})
        row['good_name'] = good_name.text if good_name else None
        price = item.find('span', {"class": "price-new"})
        if price is None:
            price = item.find('div', {'class': 'price'})
        row['price'] = price.text.strip() if price else None
        old_price = item.find('span', {"class": "price-old"})
        row['old_price'] = old_price.text if old_price else None
        id1 = good_name.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    pagination = cat_soup.find('div', {'class': 'pagination'})
    if pagination:
        pagination_a = pagination.findAll('a')
        pagination_text = [p.text for p in pagination_a]
        if '>' in pagination_text:
            next_button = pagination_a[pagination_text.index('>')]
        else:
            next_button = None
    else:
        next_button = None
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### ACEFOODS ########

# Parameters
SITE_NAME = "acefoods"
BASE_URL = "http://acefoods.vn/product"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            # find_next_page(cat)


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
    categories = toppage_soup.find('nav', {'class': 'nav-sidebar'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+acefoods\.vn/product", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "row item-container"})
    if cat_div is None:
        cat_div = []
    else:
        cat_div = cat_div.find_all("div", {"class": "col-sm-4 col-lg-4 col-md-4"})
    for item in cat_div:
        row = {}
        good_name = item.find('h4')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {'style': 'color: #b69052;'})
        row['price'] = price.text.strip() if price else None
        id1 = item.find("a")
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

##### ADAYROI #####

# Parameters
SITE_NAME = "acefoods"
BASE_URL = "http://acefoods.vn/product"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            # find_next_page(cat)


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
    categories = toppage_soup.find('nav', {'class': 'nav-sidebar'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+acefoods\.vn/product", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "row item-container"})
    if cat_div is None:
        cat_div = []
    else:
        cat_div = cat_div.find_all("div", {"class": "col-sm-4 col-lg-4 col-md-4"})
    for item in cat_div:
        row = {}
        good_name = item.find('h4')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {'style': 'color: #b69052;'})
        row['price'] = price.text.strip() if price else None
        id1 = item.find("a")
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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


######## BACHHOAXANH ########

# Parameters
SITE_NAME = "bachhoaxanh"
BASE_URL = "https://www.bachhoaxanh.com/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            # find_next_page(cat)


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
    categories = toppage_soup.find('ul', {'class': 'colmenu-ul'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+bachhoaxanh\.com/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"id": "boxproduct"})
    cat_div = cat_div.findAll("li", {"class": "product"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {"class": "price"})
        row['price'] = price.span.text.strip() if price else None
        old_price = price.find('strong') if price else None
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.get('data-product')
        row['id'] = id1
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
    next_button = cat_soup.find("a", {"class": "btn", "rel": "next"})
    if next_button:
        link = re.sub(".+adayroi\.com", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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


######### CELLPHONES ##########

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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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


######## DICHONHANH ###########

# Parameters
SITE_NAME = "dichonhanh"
BASE_URL = "https://www.dichonhanh.vn"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Initiate headless web browser
    logging.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            find_next_page(cat)
    # Close browser
    BROWSER.close()
    BROWSER.service.process.send_signal(signal.SIGTERM)
    BROWSER.quit()


def fetch_html(url, file_name, path):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < 5:
            try:
                BROWSER.get(url)
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
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
    categories = toppage_soup.find('ul', {'class': 'menu-category'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+dichonhanh\.vn/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "owl-carousel-item"})
    cat_div = cat_div.findAll("div", {"class": "i_block"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('a')
        row['good_name'] = good_name.get('title') if good_name else None
        price = item.find('span', {"class": "price_feature"})
        row['price'] = price.contents[0] if price else None
        old_price = item.find('span', {"class": "price"})
        row['old_price'] = old_price.contents[0] if old_price else None
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
    next_button = cat_soup.find("a", {"aria-label": "Next"})
    if next_button:
        link = re.sub(".+dichonhanh\.vn", "", cat['directlink'])
        link = re.sub("\?page=[0-9]+", "", link)
        link = link + next_button['href']
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### DIENMAYXANH ##########

# Parameters
SITE_NAME = "dienmayxanh"
BASE_URL = "https://www.dienmayxanh.com/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    # Download topsite and get categories directories
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)



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
    categories = toppage_soup.findAll("li", attrs={'class': 'dropdown'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        next_page = {}
        link = re.sub(".+dienmayxanh\.com/", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        next_page['label'] = re.sub("\\n", "", cat.text)
        page_list.append(next_page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)

def scrap_data(cat):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    global OBSERVATION
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" + DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_ul = cat_soup.findAll("ul", {"class": "cate"})
    cat_li = [ul.findAll("li") for ul in cat_ul]
    cat_li = [item for sublist in cat_li for item in sublist]
    for item in cat_li:
        row = {}
        good_name = item.find('a').get('title')
        if good_name:
            row['good_name'] = good_name
        else:
            good_name = item.find('h3')
            row['good_name'] = good_name.contents[0] if good_name else None
        price = item.find('strong')
        row['price'] = price.text if price else None
        old_price = item.find('cite')
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.find('a')
        row['id'] = id1.get('data-pid') if id1 else None
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

######### FOODHERO ###########

# Parameters
SITE_NAME = "foodhero"
BASE_URL = "http://www.foodhero.vn"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            # find_next_page(cat)


def fetch_html(url, file_name, path, attempts_limit=10):
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
    categories = toppage_soup.find('ul', {'class': 'left-nav nav nav navbar-nav'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+foodhero\.vn/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "product-wrapper"})
    if cat_div is None:
        cat_div = []
    else:
        cat_div = cat_div.find_all("div", {"class": "col-lg-25ths col-md-25ths col-sm-4 col-xs-12"})
    for item in cat_div:
        row = {}
        good_name = item.find('div', {"class": "name"})
        row['good_name'] = good_name.text.strip() if good_name else None
        old_price = item.find('del')
        row['old_price'] = old_price.text.strip() if old_price else None
        price = item.find('div', {'class': 'price'})
        row['price'] = re.sub('.+\\n\\t\\t', '', price.text.strip()) if price else None
        id1 = item.find("a")
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

###### FPTSHOP #########

# Parameters
SITE_NAME = "fptshop"
BASE_URL = "https://fptshop.com.vn/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
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
    categories = toppage_soup.find('nav', {'class': 'fs-menu'})
    categories = categories.findAll('li')
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+fptshop\.com\.vn/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "fs-carow"})
    cat_div = cat_div.findAll("div", {"class": "fs-lapitem"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('p', {"class": "fs-ilap-pri"})
        row['price'] = price.text.strip() if price else None
        old_price = item.find('del', {"class": "fs-ilap-pridel"})
        row['old_price'] = old_price.text.strip() if old_price else None
        id1 = good_name.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    pagination = cat_soup.find('div', {'class': 'f-cmtpaging'})
    if pagination:
        current_button = pagination.find('li', {'class': 'active'})
        next_button = current_button.findNext('li')
        next_button = next_button.find('a') if next_button else None
    else:
        next_button = None
    if next_button:
        link = re.sub(".+fptshop\.com\.vn", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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


###### GCAECO #########

# Parameters
SITE_NAME = "gcaeco"
BASE_URL = "https://gcaeco.vn"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
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
    categories = toppage_soup.find('div', {'class': 'list-cate-menu'})
    categories_tag = categories.findAll('a')
    for cat in categories_tag:
        page = {}
        link = re.sub(".+gcaeco\.vn/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "product-in-store"})
    cat_div = cat_div.findAll("div", {"class": "col-lg-5-12-item"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('p', {"class": "price"})
        old_price = price.find('del')
        row['price'] = price.text.strip() if price else None
        row['old_price'] = str(old_price.text).strip() if old_price else None
        id1 = good_name.find("a")
        row['id'] = id1.get('href') if id1 else None
        location = item.find('p', {'class': 'price marker'})
        row['location'] = location.text.strip() if location else None
        brand = item.find('p', {'class': 'price shop'})
        row['brand'] = brand.text.strip() if brand else None
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
    pagination = cat_soup.find('ul', {'class': 'pagination'})
    if pagination:
        pagination_a = pagination.findAll('a')
        pagination_text = [p.text for p in pagination_a]
        if '»' in pagination_text:
            next_button = pagination_a[pagination_text.index('»')]
        else:
            next_button = None
    else:
        next_button = None
    if next_button:
        link = re.sub(".+gcaeco\.vn", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
            next_page['relativelink'] = link
            next_page['directlink'] = BASE_URL + link
            next_page['name'] = re.sub("/|\\?.=", "_", link)
            CATEGORIES_PAGES.append(next_page)


def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'location', 'brand',
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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


###### HOANG HA MOBILE #######

# Parameters
SITE_NAME = "hoanghamobile"
BASE_URL = "https://hoanghamobile.com/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
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
    categories = toppage_soup.find('div', {'class': 'nav-items'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+hoanghamobile\.com/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "list-content"})
    cat_div = cat_div.findAll("div", {"class": "list-item"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('h4')
        row['good_name'] = good_name.text if good_name else None
        price = item.find('div', {"class": "product-price"})
        row['price'] = price.text if price else None
        old_price = price.find('strike')
        row['old_price'] = old_price.text if old_price else None
        id1 = good_name.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    paging_div = cat_soup.find("div", {"class": "paging"})
    if paging_div:
        current_button = paging_div.find('a', {'class': 'current'})
        next_button = current_button.findNext('a')
    else:
        next_button = None
    if next_button:
        link = re.sub(".+hoanghamobile\.com", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### HOTDEALVN #########

# Parameters
SITE_NAME = "hotdealvn"
BASE_URL = "https://www.hotdeal.vn/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Initiate headless web browser
    logging.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
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
    categories = toppage_soup.findAll("ul", attrs={'class': 'nav main-nav'})
    categories_tag = [cat.findAll('a', {'href': re.compile(".+")})
                      for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        next_page = {}
        link = re.sub(".+hotdeal\.vn", "", cat['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        next_page['label'] = re.sub("\\n", "", cat.text)
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
    cat_div = soup.find("div", {"class": "row products"})
    if cat_div:
        cat_div = cat_div.findAll("div", {"class": re.compile("product-kind")})
    else:
        cat_div = []
    data = []
    for item in cat_div:
        row = {}
        good_name = item.find('h3', {"class": "product__title"})
        row['good_name'] = good_name.a.get("title") if good_name else None
        price_tag = item.find('span', {'class': 'price__value'})
        row['price'] = price_tag.contents[0] if price_tag else None
        old_price_tag = item.find('div', {'class': '_product_price_original'})
        old_price_tag = old_price_tag.find("span", {"class": "price__value"}) \
            if old_price_tag else None
        row['old_price'] = old_price_tag.contents[0] if old_price_tag else None
        row['id'] = item.get('id')
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### LAZADAVN ##########

# Parameters
SITE_NAME = "lazadavn"
BASE_URL = "https://www.lazada.vn/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Initiate headless web browser
    logging.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
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
    categories = toppage_soup.findAll("li", {'class': re.compile('sub-item')})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        next_page = {}
        link = re.sub(".+lazada\.vn", "", cat['href'])
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
    global OBSERVATION
    soup = BeautifulSoup(BROWSER.page_source, 'lxml')
    page_count = soup.find_all('li', class_='ant-pagination-item')
    if len(page_count) == 0:
        page_count = '0'
    else:
        page_count = page_count[len(page_count) - 1]
        page_count = page_count.get('title').strip()
    logging.debug('This category has ' + page_count + ' pages')
    try:
        i = 0
        while i < int(page_count):
            if i != 0:
                element = BROWSER.find_element_by_css_selector(
                    ".ant-pagination-next > a:nth-child(1)"
                )
                BROWSER.execute_script("arguments[0].click();", element)
                soup = BeautifulSoup(BROWSER.page_source, 'lxml')
                list = soup.find_all('div', class_='c2prKC')
            if i == 0 or i == int(page_count) - 1:
                soup = BeautifulSoup(BROWSER.page_source, 'lxml')
                list = soup.find_all('div', class_='c2prKC')
            for item in list:
                row = {}
                good_name = item.find('div', {"class": "c16H9d"})
                row['good_name'] = good_name.a.get('title') if good_name else None
                price = item.find('span', {"class": "c13VH6"})
                row['price'] = price.contents[0] if price else None
                old_price = item.find('del', {"class": "c13VH6"})
                row['old_price'] = old_price.contents[0] if old_price else None
                row['id'] = item.get('data-item-id') if item else None
                row['category'] = cat['name']
                row['category_label'] = cat['label']
                row['date'] = DATE
                OBSERVATION += 1
                write_data(row)
            i += 1
    except Exception as e:
        logging.error("Error on " + BROWSER.current_url)
        logging.info(e)
        pass


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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### NK FOOD #######

# Parameters
SITE_NAME = "nkfood"
BASE_URL = "http://nkfood.vn/cua-hang/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
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
    categories = toppage_soup.find('ul', {'id': 'menu-menu-chinh-1'})
    categories = categories.findAll('ul', {'class': 'sub-menu'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+nkfood\.vn/cua-hang/", "", cat['href'])
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
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_div = cat_soup.find("ul", {"class": "products"})
    if cat_div is None:
        cat_div = []
    else:
        cat_div = cat_div.find_all("li", {"class": "instock"})
    for item in cat_div:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('span', {'class': 'price'})
        row['price'] = price.text.strip() if price else None
        # old_price = item.find('del')
        # row['old_price'] = old_price.text.strip() if old_price else None
        id1 = item.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    next_button = cat_soup.find("a", {"class": "next page-numbers"})
    if next_button:
        link = re.sub(".+nkfood\.vn/cua-hang/", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

###### NONG SAN BAN BUON #######

# Parameters
SITE_NAME = "nongsanbanbuon"
BASE_URL = "http://nongsanbanbuon.com"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
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
    categories = toppage_soup.find('ul', {'class': 'menu-product menu-product-news'})
    categories = categories.findAll('li')
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+nongsanbanbuon\.com/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "box-item"})
    cat_div = cat_div.findAll("div", {"class": "item-product"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('h4')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('span', {"class": "price"})
        row['price'] = price.text.strip("Giá:").strip() if price else None
        location = price.findNext('p')
        row['location'] = location.text.strip() if location else None
        date_posted = location.findNext('p')
        row['date_posted'] = date_posted.text.strip() if date_posted else None
        id1 = good_name.find('a')
        row['id'] = id1.get('href') if id1 else None
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
    pagination = cat_soup.find('ul', {'class': 'page-count'})
    if pagination:
        next_button = pagination.find('li', {'class': 'next'})
        next_button = next_button.find('a') if next_button else None
    else:
        next_button = None
    if next_button:
        link = re.sub(".+nongsanbanbuon\.com", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

####### SENDO #########

# Parameters
SITE_NAME = "sendo"
BASE_URL = "https://www.sendo.vn/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())
OBSERVATION = 0


# Selenium options
OPTIONS = Options()
OPTIONS.add_argument('--headless')
OPTIONS.add_argument("--window-size=1920,1080")
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


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
        # Close browser
        BROWSER.close()
        BROWSER.service.process.send_signal(signal.SIGTERM)
        BROWSER.quit()
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global BROWSER
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Initiate headless web browser
    logging.debug('Initialize browser')
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL + 'sitemap/', base_file_name, PATH_HTML,
               attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES[:3]:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
    # close browser
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
                logging.debug('Entering ' + url)
                BROWSER.get(url)
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
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
    categories_tag = []
    html_content = BROWSER.find_element_by_xpath("/html").get_attribute("innerHTML")
    soup = BeautifulSoup(html_content, 'lxml')
    tag = dict()
    cat1s = soup.findAll('div', {'class': 'site-map-block'})
    for cat1 in cat1s:
        cat1_text = cat1.find('div', {'class': 'site-map-title'}).text.strip()
        cat2s = cat1.findAll('li', {'class': 'site-map-item'})
        for cat2 in cat2s:
            cat2_tag = cat2.find('a', {'class': 'title-lv-2'})
            cat2_text = cat2_tag.text.strip()
            cat3s = cat2.findAll('li')
            if len(cat3s) > 0:
                for cat3 in cat3s:
                    tag['text'] = cat1_text + " > " + cat2_text + \
                        " > " + cat3.text.strip()
                    tag['href'] = cat3.find('a').get('href')
                    categories_tag.append(tag.copy())
            else:
                tag['text'] = cat1_text + ">" + cat2_text
                tag['href'] = cat2_tag.get('href')
                categories_tag.append(tag.copy())

    for cat in categories_tag:
        page = {}
        link = re.sub(".+sendo\.vn/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.=", "_", link)
        page['label'] = cat['text']
        page_list.append(page)
    # Remove duplicate
    # print(page_list)
    # page_list = [dict(t) for t in {tuple(d.items()) for d in page_list}]
    return(page_list)
                    
def scrap_data(cat):
    """Get item data from a category page and write to csv"""
    global BROWSER
    global OBSERVATION
    while True:
        try:
            pagination = BROWSER.find_element_by_css_selector('.paginationForm_c7Tb')
            soup = BeautifulSoup(pagination.get_attribute("innerHTML"), 'lxml')
        except Exception as e:
            logging.debug('Wait for pagination button on ' + BROWSER.current_url)
            logging.debug(e)
            time.sleep(1)
            continue
        break
    page_count = soup.find('input').get('max')
    logging.debug('This category has ' + page_count + ' pages')
    page = 1
    while page < int(page_count):
        while True:
            try:
                element = BROWSER.find_element_by_css_selector('a.item_3KnU')
                break
            except Exception as e:
                logging.debug('Waiting for items grid to load')
                time.sleep(0.1)
                continue
        try:
            soup = BeautifulSoup(BROWSER.page_source, 'lxml')
            list = soup.find_all('a', class_='item_3KnU')
            for item in list:
                row = {}
                good_name = item.find('h3', {"class": "productName_u171"})
                row['good_name'] = good_name.text.strip() if good_name else None
                price = item.find('strong', {"class": "currentPrice_2hr9"})
                row['price'] = price.text.strip() if price else None
                old_price = item.find('strong', {"class": "oldPrice_itl0"})
                row['old_price'] = old_price.text.strip() if old_price else None
                row['id'] = re.sub(r'\.html.+', '', item.get('href'))
                seller = item.find('span', {'class': 'shopText_3O03'})
                row['seller'] = seller.text.strip() if seller else None
                row['category'] = cat['name']
                row['category_label'] = cat['label']
                row['date'] = DATE
                OBSERVATION += 1
                write_data(row)
        except Exception as e:
            logging.error("Error on " + BROWSER.current_url)
            logging.error(e)
            continue
        page += 1
        logging.debug("Entering " + cat['directlink'] + '?p=' + str(page))
        BROWSER.get(cat['directlink'] + '?p=' + str(page))
    


def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'seller', 
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

######## TAP HOA GAN NHA #########

# Parameters
SITE_NAME = "taphoagannha"
BASE_URL = "http://taphoagannha.com/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    global CATEGORIES_PAGES
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.debug("Downloaded " + file_name)
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
    categories = toppage_soup.find('div', {'class': 'nav_2'})
    categories_tag = categories.findAll('a')
    for cat in categories_tag:
        page = {}
        link = re.sub(".+taphoagannha\.com/", "", cat['href'])
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
    cat_div = cat_soup.find('div', {'id': 'listdeal'})
    if cat_div:
        cat_div = cat_div.findAll('div', {'class': 'deal_list'})
    else:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find('div', {"class": "deal_list_title"})
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {"class": "deal_list_view_price"})
        row['price'] = price.text.strip() if price else None
        old_price = item.find('em')
        row['old_price'] = old_price.text if old_price else None
        id1 = good_name.find('a')
        row['id'] = id1.get('href') if id1 else None
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
    pagination = cat_soup.find('ul', {'class': 'paginator'})
    if pagination:
        pagination_a = pagination.findAll('a')
        pagination_text = [p.text for p in pagination_a]
        if 'Trang kế' in pagination_text:
            next_button = pagination_a[pagination_text.index('Trang kế')]
        else:
            next_button = None
    else:
        next_button = None
    if next_button:
        link = re.sub(".+taphoagannha\.com", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

###### THE GIOI DI DONG #######

# Parameters
SITE_NAME = "thegioididong"
BASE_URL = "https://www.thegioididong.com/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global CATEGORIES_PAGES
    global DATE
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in CATEGORIES_PAGES:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            # find_next_page(cat)


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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.debug("Downloaded " + file_name)
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
    categories = toppage_soup.findAll("div", attrs={'class': 'navigat'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+thegioididong\.com", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.=", "_", link)
        page['label'] = cat.text
        page_list.append(page)
    # Remove duplicates
    page_list = [dict(t) for t in set(tuple(i.items()) for i in page_list)]
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    global OBSERVATION
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_ul = cat_soup.findAll("ul", {"class": "homeproduct"})
    cat_li = [ul.findAll("li") for ul in cat_ul]
    cat_li = [item for sublist in cat_li for item in sublist]
    data = []
    for item in cat_li:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.contents[0] if good_name else None
        price_tag = item.find('strong')
        price = price_tag.contents if price_tag else []
        row['price'] = price[0] if len(price) > 0 else None
        old_price_tag = price_tag.find_next_sibling('span')
        old_price = old_price_tag.contents if old_price_tag else []
        row['old_price'] = old_price[0]\
            if len(old_price) > 0 else None
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

###### TIKI #######

# Parameters
site_name = "tiki"
base_url = "https://tiki.vn/"
project_path = re.sub("/py$", "", os.getcwd())
path_html = project_path + "/html/" + site_name + "/"
path_csv = project_path + "/csv/" + site_name + "/"


def daily_task():
    """Main workhorse function. Support functions defined below"""
    # Download topsite and get categories directories
    date = str(datetime.date.today())
    base_file_name = "All_cat_" + date + ".html"
    fetch_html(base_url, base_file_name, path_html)
    html_file = open(path_html + base_file_name).read()
    cat_link = get_category_list(html_file)
    cat_name = [re.sub("/|\\?.=", "_", link) for link in cat_link]
    # Download categories pages and scrap for data
    price_data = []
    for link, name in zip(cat_link, cat_name):
        cat_file = "cat_" + name + "_" + date + ".html"
        fetch_html(base_url + link, cat_file, path_html)
        if os.path.isfile(path_html + cat_file) is True:
            price_data.append(scrap_data(name))
    price_data = [item for sublist in price_data for item in sublist]
    # Write csv
    if not os.path.exists(path_csv):
        os.makedirs(path_csv)
    with open(path_csv + site_name + "_" + date + ".csv", "w") as f:
        fieldnames = ['good_name', "id", 'price',
                      'old_price', 'category', 'date']
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(price_data)
    # Compress data
    zip_csv = "cd " + path_csv + "&& tar -cvzf " + site_name + "_" + \
        date + ".tar.gz *" + site_name + "_" + date + "* --remove-files"
    zip_html =  "cd " + path_html + "&& tar -cvzf " + site_name + "_" + \
        date + ".tar.gz *" + date + ".html* --remove-files"
    os.system(zip_csv)
    os.system(zip_html)


def fetch_html(url, file_name, path):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < 5:
            try:
                con = urlopen(url, timeout=5)
                html_content = con.read()
                with open(path + file_name, "wb") as f:
                    f.write(html_content)
                    con.close
                print("Downloaded ", file_name)
                break
            except:
                attempts += 1
                print("Try again", file_name)
        else:
            print("Cannot download", file_name)
    else:
        print("Already downloaded ", file_name)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.find("nav", {'class': 'main-nav-wrap'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories_link = [re.sub(".+tiki\.vn/", "", i['href'])
                       for i in categories_tag]
    categories_link = list(set(categories_link))  # Remove duplicates
    return(categories_link)


def scrap_data(cat_name):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    date = str(datetime.date.today())
    cat_file = open(path_html + "cat_" + cat_name + "_" + date + ".html")\
        .read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_div = cat_soup.find("div", {"class": "product-box-list"})
    if cat_div:
        cat_div = cat_div.findAll("div", {"class": "product-item"})
    else: cat_div = []
    data = []
    for item in cat_div:
        if 'flash-sale' in item.get('class'):
            continue
        row = {}
        row['good_name'] = item.get('data-title')
        if not row['good_name']:
            good_name = item.find("a")
            row['good_name'] = good_name.get('title') if good_name else None
        price = item.find('span', {'class': 'final-price'})
        row['price'] = price.contents[0] if price else None
        old_price = item.find('span', {"class": 'price-regular'})
        row['old_price'] = old_price.contents[0] if old_price else None
        row['id'] = item.get('data-seller-product-id') if item else None
        row['category'] = cat_name
        row['date'] = date
        data.append(row)
    return(data)


if "test" in sys.argv:
    daily_task()
else:
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

######### VINMART ###########

# Parameters
SITE_NAME = "vinmart"
BASE_URL = "https://www.adayroi.com/vinmart"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    global CATEGORIES_PAGES
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.debug("Downloaded " + file_name)
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
    categories = toppage_soup.find('ul', {'class': 'navbar-nav'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+adayroi\.com/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = "https://www.adayroi.com/" + link
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
    cat_div = cat_soup.find("div", {"class": "product-list__container"})
    cat_div = cat_div.find("div", {"class": "row"}) if cat_div else None
    if cat_div is None:
        cat_div = []
    for item in cat_div:
        row = {}
        good_name = item.find(re.compile('a|h3'),
                              {"class": "product-item__info-title"})
        row['good_name'] = good_name.contents[0] if good_name else None
        price = item.find('span', {"class": "product-item__info-price-sale"})
        row['price'] = price.contents[0] if price else None
        old_price = item.find('span',
                              {"class": "product-item__info-price-original"})
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    next_button = cat_soup.find("a", {"class": "btn", "rel": "next"})
    if next_button:
        link = re.sub(".+adayroi\.com", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
            next_page['relativelink'] = link
            next_page['directlink'] = "https://www.adayroi.com/" + link
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

###### VNSHOP #######

# Parameters
SITE_NAME = "vnshop"
BASE_URL = "https://vnshop.vn/"
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
        logging.exception('Got exception, scraper stopped')
        logging.info(e)
    # Compress data and html files
    compress_csv()
    compress_html()
    logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    global CATEGORIES_PAGES
    global OBSERVATION
    logging.info('Scraper started')
    # Refresh date
    DATE = str(datetime.date.today())
    OBSERVATION = 0
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML, attempts_limit=1000)
    html_file = open(PATH_HTML + base_file_name).read()
    CATEGORIES_PAGES = get_category_list(html_file)
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
                logging.debug("Downloaded " + file_name)
                return(True)
            except:
                attempts += 1
                logging.debug("Downloaded " + file_name)
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
    categories = toppage_soup.find('ul', {'id': 'nav'})
    categories = categories.findAll('li', {'class': 'h3'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+vnshop\.vn/", "", cat['href'])
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
    cat_div = cat_soup.find("div", {"class": "row"})
    if cat_div is None:
        cat_div = []
    else:
        cat_div = cat_div.find_all("div", {"class": "product-box"})
    for item in cat_div:
        row = {}
        good_name = item.find('h3')
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('div', {'class': 'special-price'})
        row['price'] = price.text.strip() if price else None
        old_price = item.find('div', {'class': 'old-price'})
        row['old_price'] = old_price.text.strip() if old_price else None
        id1 = good_name.find("a")
        row['id'] = id1.get('href') if id1 else None
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
    button = cat.find('ul', {'class': 'pagination'})
    if button:
        next_button = cat_soup.find_all("a", {"class": "hidden-xs"})[-1]
    if next_button:
        link = re.sub(".vnshop\.vn/", "", next_button['href'])
        if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
            next_page = cat.copy()
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
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(e)
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

#############################################################