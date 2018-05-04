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
site_name = "dienmayxanh"
base_url = "https://www.dienmayxanh.com"
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
        cat_file = "cat" + name + "_" + date + ".html"
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
    categories = toppage_soup.findAll("li", attrs={'class': 'dropdown'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories_link = [re.sub(".+dienmayxanh\.com/", "", i['href'])
                       for i in categories_tag]
    categories_link = list(set(categories_link))  # Remove duplicates
    return(categories_link)


def scrap_data(cat_name):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    date = str(datetime.date.today())
    cat_file = open(path_html + "cat" + cat_name + "_" + date + ".html").read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_ul = cat_soup.findAll("ul", {"class": "cate"})
    cat_li = [ul.findAll("li") for ul in cat_ul]
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
        price = item.find('strong')
        row['price'] = price.contents[0] if price else None
        old_price = item.find('cite')
        row['old_price'] = old_price.contents[0] if old_price else None
        id1 = item.find('a')
        row['id'] = id1.get('data-pid') if id1 else None
        row['category'] = cat_name
        row['date'] = date
        data.append(row)
    return(data)


if "test" in sys.argv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)
