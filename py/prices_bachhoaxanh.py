import sys
import os
import time
import datetime
import schedule
import re
import csv
import random
import coloredlogs, logging
from urllib.request import urlopen
from bs4 import BeautifulSoup


# Parameters
SITE_NAME = "bachhoaxanh"
BASE_URL = "https://www.bachhoaxanh.com/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"


# Setting up logging
log_format = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p'
)
log_writer = logging.FileHandler(PATH_LOG + SITE_NAME + '.log')
log_stout = logging.StreamHandler()
log_error = logging.FileHandler(PATH_LOG + 'aggregated_error/errors.log')

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
        logging.info('Hibernating...')


def daily_task():
    """Main workhorse function. Support functions defined below"""
    # Download topsite and get categories directories
    date = str(datetime.date.today())
    base_file_name = "All_cat_" + date + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML)
    html_file = open(PATH_HTML + base_file_name).read()
    cat_link = get_category_list(html_file)
    logging.info('Found ' + str(len(CATEGORIES_PAGES)) + ' categories')
    cat_name = [re.sub("/|\\?.=", "_", link) for link in cat_link]
    # Download categories pages and scrap for data
    price_data = []
    for link, name in zip(cat_link, cat_name):
        cat_file = "cat" + name + "_" + date + ".html"
        fetch_html(BASE_URL + link, cat_file, PATH_HTML)
        if os.path.isfile(PATH_HTML + cat_file) is True:
            price_data.append(scrap_data(name))
    price_data = [item for sublist in price_data for item in sublist]
    # Write csv
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + date + ".csv", "w") as f:
        fieldnames = ['good_name', "id", 'price',
                      'old_price', 'category', 'date']
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(price_data)
    # Compress data
    zip_csv = "cd " + PATH_CSV + "&& tar -cvzf " + SITE_NAME + "_" + \
        date + ".tar.gz *" + SITE_NAME + "_" + date + "* --remove-files"
    zip_html =  "cd " + PATH_HTML + "&& tar -cvzf " + SITE_NAME + "_" + \
        date + ".tar.gz *" + date + ".html* --remove-files"
    os.system(zip_csv)
    os.system(zip_html)
    logging.info('Scraper finished, hibernating...')


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
                logging.debug("Downloaded " + file_name)
                break
            except:
                attempts += 1
                logging.warning("Try again" + file_name)
        else:
            logging.error("Cannot download" + file_name)
    else:
        logging.debug("Already downloaded " + file_name)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.findAll("ul", {'class': 'dropdown-menu-aim'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories_link = [re.sub(".+bachhoaxanh\.com/", "", i['href'])
                       for i in categories_tag]
    categories_link = list(set(categories_link))  # Remove duplicates
    return(categories_link)


def scrap_data(cat_name):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    date = str(datetime.date.today())
    cat_file = open(PATH_HTML + "cat" + cat_name + "_" + date + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_ul = cat_soup.findAll("ul", {"class": "cate"})
    cat_li = [ul.findAll("li", {"class": "item"}) for ul in cat_ul]
    cat_li = [item for sublist in cat_li for item in sublist]
    data = []
    for item in cat_li:
        row = {}
        good_name = item.find('a').get('title')
        if good_name:
            row['good_name'] = good_name
        else:
            good_name = item.find('h3')
            row['good_name'] = good_name.contents[0] if good_name else None
        price = item.find("div", {"class": "rowprice"})
        price = price.strong if price else None
        row['price'] = price.contents[0] if price else None
        old_price = item.find('cite')
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.find('a')
        row['id'] = id1.get('href') if id1 else None
        row['category'] = cat_name
        row['date'] = date
        data.append(row)
    return(data)


if "test" in sys.argv:
    main()
else:
    start_time = '06:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
