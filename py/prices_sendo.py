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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
import signal


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
        # Close browser
        BROWSER.close()
        BROWSER.service.process.send_signal(signal.SIGTERM)
        BROWSER.quit()
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
                               options=OPTIONS)
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL + 'sitemap/', base_file_name, PATH_HTML,
               attempts_limit=1000)
    BROWSER.get("https://www.sendo.vn/sitemap/")
    CATEGORIES_PAGES = get_category_list()
    log.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    # Read each categories pages and scrape for data
    for cat in track(CATEGORIES_PAGES,
                     description = "[green]Scraping...",
                     total = len(CATEGORIES_PAGES)):
        # cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        # download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        # if download:
        scrap_data(cat)
    # close browser
    BROWSER.close()
    BROWSER.service.process.send_signal(signal.SIGTERM)
    BROWSER.quit()


def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    global BROWSER
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                log.debug('Entering ' + url)
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
    categories_tag = []
    tag = dict()
    cat1s = BROWSER.find_elements_by_css_selector('div.item_3GwX')
    for cat1 in track(cat1s, description="[green]Get categories..."):
        cat1_text = cat1.find_element_by_css_selector('h3').text.strip()
        cat2s = cat1.find_elements_by_css_selector('a.cat_2URx')
        for cat2 in cat2s:
            cat2_text = cat2.text.strip()
            while True:
                try:
                    ActionChains(BROWSER).move_to_element(cat2).perform()
                    cat2.click()
                except WebDriverException:
                    time.sleep(2)
                    btn = BROWSER.switch_to_active_element()
                    btn = btn.find_element_by_css_selector('button.closeBtn_2s1w')
                    log.info("Popup shown at " + BROWSER.current_url)
                    btn.click()
                    time.sleep(1)
                    continue
                break
            time.sleep(1)
            cat3s = cat1.find_elements_by_css_selector('li.mounted_YTF6')
            if len(cat3s) > 0:
                for cat3 in cat3s:
                    tag['text'] = cat1_text + " > " + cat2_text + \
                        " > " + cat3.text.strip()
                    tag['href'] = cat3.find_element_by_css_selector('a')\
                                      .get_attribute('href')
                    categories_tag.append(tag.copy())
            else:
                tag['text'] = cat1_text + ">" + cat2_text
                tag['href'] = cat2.get_attribute('href')
                categories_tag.append(tag.copy())
    # Unifying categories info into dicts
    for cat in categories_tag:
        page = {}
        link = re.sub(r".+sendo\.vn/", "", cat['href'])
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
    BROWSER.get(cat['directlink'])
    while True:
        try:
            pagination = BROWSER.find_element_by_css_selector('div.paginationForm_c7Tb input')
            soup = BeautifulSoup(pagination.get_attribute("innerHTML"), 'lxml')
        except Exception as e:
            log.debug('Wait for pagination button on ' + BROWSER.current_url)
            log.debug(e)
            time.sleep(1)
            continue
        break
    page_count = pagination.get_attribute('max')
    log.debug('This category has ' + page_count + ' pages')
    page = 1
    while page < int(page_count):
        while True:
            try:
                BROWSER.find_element_by_css_selector('div.ReactVirtualized__Grid__innerScrollContainer')
                break
            except Exception as e:
                log.debug('Waiting for items grid to load')
                time.sleep(2)
                continue
        try:
            soup = BeautifulSoup(BROWSER.page_source, 'lxml')
            list = soup.find_all('a', class_='item_3x07')
            for item in list:
                row = {}
                good_name = item.find('h3', {"class": "productName_u171"})
                row['good_name'] = good_name.text.strip() if good_name else None
                price = item.find('strong', {"class": "currentPrice_2hr9"})
                row['price'] = price.text.strip() if price else None
                old_price = item.find('strong', {"class": "oldPrice_itl0"})
                row['old_price'] = old_price.text.strip() if old_price else None
                row['id'] = re.sub(r'\.html.+', '', item.get('href'))
                seller = item.find('span', {'class': 'shopName_4r40'})
                row['seller'] = seller.text.strip() if seller else None
                location = item.find('span', {'class': 'locationName_3SN5'})
                row['location'] = seller.text.strip() if location else None
                row['category'] = cat['name']
                row['category_label'] = cat['label']
                row['date'] = DATE
                OBSERVATION += 1
                write_data(row)
        except WebDriverException:
            time.sleep(2)
            btn = BROWSER.switch_to_active_element()
            btn = btn.find_element_by_css_selector('button.closeBtn_2s1w')
            log.info("Popup shown at " + BROWSER.current_url)
            btn.click()
            time.sleep(1)
            continue
        except Exception as e:
            log.error(e)
            log.error("Error on " + BROWSER.current_url)
            continue
        page += 1
        BROWSER.get(cat['directlink'] + '?p=' + str(page))
    

def write_data(item_data):
    """Write an item data as a row in csv. Create new file if needed"""
    fieldnames = ['good_name', 'price', 'old_price', 'id', 'seller', 
                  'location', 'category', 'category_label', 'date']
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
