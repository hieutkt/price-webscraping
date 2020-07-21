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
import coloredlogs
import logging
import logging.handlers as handlers
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import signal


# Parameters
SITE_NAME = "adayroi"
BASE_URL = "https://www.adayroi.com/"
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
log_error = handlers.TimedRotatingFileHandler(
    PATH_LOG + 'aggregated_error/errors.log',
    when='midnight', interval=1)
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
        logging.info(type(e).__name__ + e)
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
            find_next_page(cat)
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
            except Exception as e:
                logging.info(type(e).__name__ + e)
                logging.warning("Try again" + file_name)
                attempts += 1
        else:
            logging.error("Cannot download" + file_name)
            return(False)
    else:
        logging.debug("Already downloaded " + file_name)
        return(True)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    tag = dict()
    categories_tag = []
    cat1s = BROWSER\
        .find_elements_by_css_selector("ul.menu__cat:nth-child(1) > li")
    for cat1 in cat1s:
        cat1_text = cat1.text.strip()
        # print(cat1_text)
        hover = ActionChains(BROWSER).move_to_element(cat1)
        hover.perform()
        time.sleep(1)
        while True:
            cat2s = cat1.find_elements_by_css_selector('.sub-category__item')
            if len(cat2s) > 0:
                break
            else:
                cat2s = cat1\
                    .find_elements_by_css_selector('sub-category__item')
                time.sleep(1)
                continue
        for cat2 in cat2s:
            cat2_text = cat2.find_element_by_css_selector('a.h13-bo-20')\
                            .text\
                            .strip()
            cat3s = cat2.find_elements_by_css_selector(".mt-3")
            if len(cat3s) > 0:
                for cat3 in cat3s:
                    cat3_text = cat3.text.strip()
                    tag['text'] = cat1_text + ">" + cat2_text + ">" + cat3_text
                    tag['href'] = cat3.find_element_by_css_selector('a')\
                                      .get_attribute('href')
                    categories_tag.append(tag.copy())
            else:
                tag['text'] = cat1_text + ">" + cat2_text
                tag['href'] = cat2.find_element_by_css_selector('a.h13-bo-20')\
                                  .get_attribute('href')
                categories_tag.append(tag.copy())
    for cat in categories_tag:
        page = {}
        link = re.sub(".+adayroi\\.com/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.=", "_", link)
        page['label'] = cat['text']
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
        link = re.sub(".+adayroi\\.com", "", next_button['href'])
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
        zip_csv = ZipFile(SITE_NAME + '_' + DATE + '_csv.zip', 'a')
        for file in glob.glob("*" + DATE + "*" + "csv"):
            zip_csv.write(file)
            os.remove(file)
        logging.info("Compressing " + str(OBSERVATION) + " item(s)")
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(type(e).__name__ + e)
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
        logging.info("Compressing HTML files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(type(e).__name__ + e)
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
