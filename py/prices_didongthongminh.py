import sys
import os
import time
import datetime
import schedule
import re
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Parameters
SITE_NAME = "didongthongminh"
BASE_URL = "https://didongthongminh.vn/"
PROJECT_PATH = re.sub("/py$", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"

# Selenium options
OPTIONS = Options()
# OPTIONS.add_argument('--headless')
OPTIONS.add_argument('--disable-gpu')
CHROME_DRIVER = PROJECT_PATH + "/bin/chromedriver"  # Chromedriver v2.38


def daily_task():
    """Main workhorse function. Support functions defined below"""
    global DATE
    global CATEGORIES_PAGES
    global BROWSER
    DATE = str(datetime.date.today())
    # Initiate headless web browser
    BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
                               chrome_options=OPTIONS)
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
    # Compress data and html files
    compress_data()


def fetch_html(url, file_name, path, attempts_limit=5):
    """Fetch and download a html with provided path and file names"""
    if not os.path.exists(path):
        os.makedirs(path)
    if os.path.isfile(path + file_name) is False:
        attempts = 0
        while attempts < attempts_limit:
            try:
                BROWSER.get(url)
                print("Browsed", url)
                time.sleep(2)
                is_more = True
                while is_more:
                    print('Finding more button')
                    more_button = BROWSER.find_elements_by_css_selector('#sb-infinite-scroll-load-more-1')
                    if more_button:
                        more_button = more_button[0].find_element_by_css_selector("a[sb-processing='0']")
                        if 'Xem thêm' in more_button.text:
                            print("Click to show more")
                            more_button.click()
                            time.sleep(5)
                        else:
                            print('Button found but no more item:', more_button.text)
                            is_more = False
                    else:
                        print('No button')
                        is_more = False
                element = BROWSER.find_element_by_xpath("/html")
                html_content = element.get_attribute("innerHTML")
                with open(path + file_name, "w") as f:
                    f.write(html_content)
                print("Downloaded ", file_name)
                return(True)
            except Exception as e:
                print(e)
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
    categories = toppage_soup.find('div', {'id': 'dstbar'})
    categories = categories.findAll('li')
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    for cat in categories_tag:
        page = {}
        link = re.sub(".+didhongthongminh\.vn/", "", cat['href'])
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
    cat_ul = cat_soup.findAll("ul", {"class": "products"})
    cat_li = [ul.findAll('li') for ul in cat_ul]
    cat_li = [item for sublist in cat_li for item in sublist]
    print("Scraping", len(cat_li), "items...")
    for item in cat_li:
        row = {}
        good_name = item.find('span', {"class": "dst_primtitle"})
        row['good_name'] = good_name.text.strip() if good_name else None
        price = item.find('span', {"class": "price"})
        row['price'] = price.text.strip() if price else None
        # old_price = item.find('span', {"class": "price-old"})
        # row['old_price'] = old_price.text if old_price else None
        id1 = item.find("a")
        row['id'] = id1.get('href') if id1 else None
        row['category'] = cat['name']
        row['category_label'] = cat['label']
        row['date'] = DATE
        write_data(row)


# def find_next_page(cat):
#     """Find the next page button, return page data"""
#     cat_file = open(PATH_HTML + "cat_" + cat['name'] + "_" +
#                     DATE + ".html").read()
#     cat_soup = BeautifulSoup(cat_file, "lxml")
#     pagination = cat_soup.find('div', {'class': 'pagination'})
#     if pagination:
#         pagination_a = pagination.findAll('a')
#         pagination_text = [p.text for p in pagination_a]
#         if '>' in pagination_text:
#             next_button = pagination_a[pagination_text.index('>')]
#         else:
#             next_button = None
#     else:
#         next_button = None
#     if next_button:
#         link = re.sub(".+123wow\.vn", "", next_button['href'])
#         if link not in [i['relativelink'] for i in CATEGORIES_PAGES]:
#             next_page = cat.copy()
#             next_page['relativelink'] = link
#             next_page['directlink'] = BASE_URL + link
#             next_page['name'] = re.sub("/|\\?.=", "_", link)
#             CATEGORIES_PAGES.append(next_page)


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
