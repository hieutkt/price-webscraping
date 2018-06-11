import sys
import os
import time
import datetime
import schedule
import re
import csv
from urllib.request import urlopen
from bs4 import BeautifulSoup


# Parameters
SITE_NAME = "adayroi"
BASE_URL = "https://www.adayroi.com/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    DATE = str(datetime.date.today())
    # Download topsite and get categories directories
    base_file_name = "All_cat_" + DATE + ".html"
    fetch_html(BASE_URL, base_file_name, PATH_HTML)
    html_file = open(PATH_HTML + base_file_name).read()
    categories = get_category_list(html_file)
    # Read each categories pages and scrape for data
    for cat in categories:
        cat_file = "cat_" + cat['name'] + "_" + DATE + ".html"
        download = fetch_html(cat['directlink'], cat_file, PATH_HTML)
        if download:
            scrap_data(cat)
            next_page = find_next_page(cat)
            if next_page is not None and\
               next_page['directlink'] not in\
               [i['directlink'] for i in categories]:
                categories.append(next_page)
    # Compress data and html files
    compress_data()


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
                return(True)
            except:
                attempts += 1
                print("Try again", file_name)
        else:
            print("Cannot download", file_name)
            return(False)
    else:
        print("Already downloaded ", file_name)
        return(True)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    page_list = []
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.find('ul', {'class': 'menu__cat-list'})
    categories = categories.findAll("li")
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+adayroi\.com/", "", cat['href'])
        page['relativelink'] = link
        page['directlink'] = BASE_URL + link
        page['name'] = re.sub("/|\\?.=", "_", link)
        label = cat.find("span", {"class": "infor-sale"})
        if label:
            page['label'] = label.contents[0]
        else:
            page['label'] = cat.contents[0]
        page_list.append(page)
    return(page_list)


def scrap_data(cat):
    """Get item data from a category page and write to csv"""
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
        write_data(row)


def find_next_page(cat):
    """Find the next page button, return page data"""
    cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
                    DATE + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    next_page = cat.copy()
    next_button = cat_soup.find("a", {"class": "btn", "rel": "next"})
    if next_button:
        link = re.sub(".+adayroi\.com", "", next_button['href'])
        next_page['relativelink'] = link
        next_page['directlink'] = BASE_URL + link
        next_page['name'] = re.sub("/|\\?.=", "_", link)
        return(next_page)
    else:
        return(None)


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
