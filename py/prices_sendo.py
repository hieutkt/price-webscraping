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
from urllib.request import urlopen
from bs4 import BeautifulSoup


# Parameters
SITE_NAME = "sendo"
BASE_URL = "https://www.sendo.vn/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
PATH_LOG = PROJECT_PATH + "/log/"
DATE = str(datetime.date.today())


# Setting up logging
def setup_log
log_format = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p'
)
log_writer = logging.FileHandler(PATH_LOG + SITE_NAME + '.log')
log_stout = logging.StreamHandler()
log_error = handlers.TimedRotatingFileHandler(PATH_LOG + 'aggregated_error/errors.log',
    when = 'midnight', interval=1)
log_error.suffix = '%Y-%m-%d'

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
    categories = toppage_soup.findAll("li", attrs={'class': 'menuItem'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories_link = [re.sub(".+sendo\.vn/", "", i['href'])
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
    cat_div = cat_soup.find("div", {"class": "box-listing"})
    if cat_div:
        cat_div = cat_div.findAll("div", {"class": re.compile("box_product")})
    else: cat_div = []
    data = []
    for item in cat_div:
        row = {}
        good_name = item.find('a', {"class": re.compile("name_product")})
        row['good_name'] = good_name.get('title') if good_name else None
        price = item.find('span', {"class": "current_price"})
        row['price'] = price.contents[0] if price else None
        old_price = item.find('span', {"class": "old_price"})
        row['old_price'] = old_price.contents[0] if old_price else None
        row['id'] = item.get('id') if item else None
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
