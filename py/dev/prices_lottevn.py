import os
import datetime
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup


def fetch_html(url, file_name, path):
    """Fetch and download a html with provided path and file names"""
    os.makedirs(path, exist_ok=True)
    if os.path.isfile(path + file_name) is False:
        try:
            con = urlopen(url)
            html_content = con.read()
            with open(path + file_name, "wb") as f:
                f.write(html_content)
                con.close
            print("Downloaded ", file_name)
        except:
            print("Cannot download ", url)
    else:
        print("Already downloaded ", file_name)


def get_category_list(top_html):
    """Get list of relative categories directories from the top page"""
    toppage_soup = BeautifulSoup(top_html, "lxml")
    categories = toppage_soup.findAll("li", attrs={'class': 'dropdown-menu'})
    categories_tag = [cat.findAll('a') for cat in categories]
    categories_tag = [item for sublist in categories_tag for item in sublist]
    categories_link = [i['href'] + '?hitsPerPage=120' for i in categories_tag]
    categories_link = list(set(categories_link))  # Remove duplicates
    return(categories_link)


def scrap_data(cat_name):
    """Get item data from a category page.
    Requires downloading the page first.
    """
    cat_path = path_html + "cat" + cat_name + "_" + date + ".html"
    if os.path.isfile(cat_path) is False:
        print("File is not downloaded ", cat_name)
        cat_file = ""
    else:
        cat_file = open(cat_path).read()
    cat_soup = BeautifulSoup(cat_file, "lxml")
    cat_a = cat_soup.findAll("a", {"class": re.compile("item-product")})
    data = []
    for item in cat_a:
        try:
            name = item.find('a', {"class": "product-item-link"})\
                       .get('title').replace(";", "")
            price = item.find('span', {"class": "final-price"}).contents[0]
            id1 = item.get('href')
            data_row = name+";"+id1+";"+price+";"+cat_name+";"+date+"\n"
            data.append(data_row)
        except AttributeError:
            continue
        except:
            print("Failed to get data from item: " + cat_name)
            continue
    return(data)


# Parameters
site_name = "lottevn"
base_url = "https://www.lotte.vn/"
date = str(datetime.date.today())
path_html = os.getcwd() + "/html/" + site_name + "/"
path_csv = os.getcwd() + "/csv/"

# Download topsite and get categories directories
base_file_name = "All_cat_" + date + ".html"
fetch_html(base_url, base_file_name, path_html)

html_file = open(path_html + base_file_name).read()
cat_link = get_category_list(html_file)
cat_name = [re.sub("/|\\?.=", "_", link) for link in cat_link]

# Download categories sites and scrap for data
for link, name in zip(cat_link, cat_name):
    fetch_html(base_url + link, "cat" + name +
               "_" + date + ".html", path_html)

price_data = [scrap_data(name) for name in cat_name]
price_data = [item for sublist in price_data for item in sublist]

# Write and compress data
os.makedirs(path_csv, exist_ok=True)

with open(path_csv + site_name + "_" + date + ".csv", "w") as f:
    f.write("good_name;id;price;category;date\n")
    for item in price_data:
        f.write(item)

zipcommand = "cd " + path_csv + "&& tar -cvzf " + site_name + \
    date + ".tar.gz *" + date + "* --remove-files"
os.system(zipcommand)
