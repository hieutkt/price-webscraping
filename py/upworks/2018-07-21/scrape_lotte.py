import csv
import datetime
import logging
import re
import zipfile
import sys
import schedule
import time
import os
from os import listdir, path
from os.path import dirname
from os.path import join
from time import sleep
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver import ChromeOptions, DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# SETTINGS FOR PROJECT
SITE_NAME = 'lottevn'

TIMEOUT = 30

PROJECT_DIR = re.sub("/py.+", "", os.getcwd())

OUTPUT_HTML_PATH =  PROJECT_DIR + "/html/" + SITE_NAME + "/"

CHROME_DRIVER_PATH = PROJECT_DIR + '/bin/chromedriver'

TEST_HTML_FILES_DIR = join(PROJECT_DIR, 'tests', 'html_pages_for_test')

OUTPUT_CSV_PATH = PROJECT_DIR + "/csv/" + SITE_NAME + "/lottevn.csv"

HEADERS = ['date', 'id', 'good_name', 'category', 'category_label', 'price', 'old_price']

# DRIVER SETTINGS
chrome_options = ChromeOptions()

# chrome_options.add_argument('headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('headless')
chrome_options.add_argument("start-maximized")


CHROME_DRIVER = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_options)


# Logging configuration
LOG_FILE = ''
# LOG_FILE = join(PROJECT_DIR, 'logs.log') # uncomment this line to output logs to FILE
LOG_LEVEL = logging.INFO  # can be set to logging.DEBUG to see all the flow
LOG_FORMAT = '%(asctime)s;%(name)s;%(levelname)s: %(message)s'


# DOWNLOADER BLOCK


class PageWalker:
    """
    object created for getting and saving html pages for list of links
    includes checking if the js on the page was loaded

    """

    def __init__(self, driver, expected_condition):
        self.driver = driver
        self.expected_condition = expected_condition

    def load_page(self, link):
        self.driver.get(link)
        self.set_check_waits(self.expected_condition)

    def get_page(self):
        self.set_check_waits(self.expected_condition)
        return self.driver.page_source

    def set_check_waits(self, expected_condition):
        el = WebDriverWait(self.driver,
                      TIMEOUT, poll_frequency=1).until(expected_condition)
        return el

    @staticmethod
    def save_page(_path, string):
        with open(_path, 'w') as f:
            f.write(string)

    @staticmethod
    def generate_desc_path(link):
        # function to generate descriptive path

        name_file = link.split('/')[-1] if link.endswith('.html') else link.split('/')[-1] + '.html'
        return join(OUTPUT_HTML_PATH, name_file)

    def process_link(self, link):
        html_body = self.get_page()
        save_path = self.generate_desc_path(link)
        self.save_page(save_path, html_body)
        LOGGER.debug('html page saved, path:%s' % save_path)
        return save_path


# EXTRACTOR BLOCK


class LotteExtractor:

    def __init__(self, input_html_path, field_loader):
        """
        class which purpose is to read html file
        :param input_html_path:
        """
        self.input_html_path = input_html_path
        self.field_loader = field_loader
        # with open(self.input_html_path, 'r') as f:
        self.tree = etree.parse(self.input_html_path, parser=etree.HTMLParser())

    def scrape_values(self, element):
        # function to scrape html file and save scraped values
        for field in self.field_loader:
            if field.xpath.startswith('/'):
                value = self.tree.findall(field.xpath) if field.xpath else None
            else:
                value = element.findall(field.xpath) if field.xpath else None
            field.add_extracted_value(value)

    def output_values(self):
        d = self.field_loader.form_dict()  # form dictionary externally in FieldLoader() obj
        LOGGER.debug('item scraped \n %s' % d)
        return d


class FieldLoader:

    def __init__(self):
        self.fields_list = []

    def __iter__(self):
        for field in self.fields_list:
            yield field

    def add_field(self, field_to_extract):
        self.fields_list.append(field_to_extract)

    def form_dict(self):
        """returns dictionary in format {'column1':'value1', 'column2':'value2'}
        for further processing"""
        d = {}
        for field in self.fields_list:
            d.update({field.column: field.value})
        return d


class FieldToExtract:
    """
    class created to help extract, save and process fields before output
    """

    def __init__(self, column, xpath, adjust_func=None):

        self.column = column
        self.xpath = xpath
        self.value = None
        if adjust_func:
            self.adjust_func = adjust_func

    def add_extracted_value(self, selector):
        if hasattr(self, 'adjust_func'):
            self.value = self.adjust_func(selector)
        else:
            self.value = selector.extract_first()
        return self.value


# MAIN BLOCK

def get_categories(driver):
    base_url = 'https://www.lotte.vn/category/170/suc-khoe-lam-dep'
    driver.get(base_url)
    # wait until page loads
    WebDriverWait(driver, timeout=TIMEOUT, poll_frequency=1).until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="subcate-content"]//li/a')))
    follow_elements = driver.find_elements_by_xpath('//div[@class="subcate-content"]//li/a')
    categories_links = [element.get_attribute('href') for element in follow_elements]
    return categories_links


def load_pages(driver, category_link):
    page_walker = PageWalker(driver, expected_condition=EC.visibility_of_element_located((
        By.XPATH, '//a[@class="button-border"]')))
    driver.get(category_link)
    LOGGER.info('loading pages for category %s' % category_link)
    page = 0
    retried =0
    while True:
        try:
            load_process =page_walker.set_check_waits(EC.visibility_of_element_located(
                (By.XPATH, '//div[@class="product-showed-bar"]/p'))).text
            loaded, to_load = re.search(r'([\d]+)/([\d]+)', load_process).group(1, 2) # grab how many products loaded
            LOGGER.info('products loaded %s of %s' % (loaded, to_load))
            page_walker.set_check_waits(EC.element_to_be_clickable((
                By.XPATH, '//a[@class="button-border"]')))
        except TimeoutException:
            retried+=1
            if retried == 5:
                LOGGER.info('category scraped')
                break
        saved_path = page_walker.generate_desc_path(driver.current_url)
        page_walker.save_page(saved_path, driver.page_source)
        page+=1
        driver.get(category_link + '?page=%s'%page)
        yield saved_path  # this is path of saved html file


def scrape_page(html_file_path, field_loader):
    extractor = LotteExtractor(input_html_path=html_file_path,
                               field_loader=field_loader)
    product_elements = extractor.tree.findall(
        '//div[@class="products-cate-list"]//div[@class="item-product"]')
    for product_el in product_elements:
        extractor.scrape_values(element=product_el)
        product_dict = extractor.output_values()
        yield product_dict


def declare_fields():
    field_loader = FieldLoader()

    # declare needed fields

    field_loader.add_field(FieldToExtract(
        column='id',
        xpath='.//a',
        adjust_func=lambda x: re.search(r'product/([\d]+)/',x[0].attrib['href']).group(1)
    ))
    field_loader.add_field(FieldToExtract(
        column='category',
        xpath='//li[@class="subcate"]',
        adjust_func=lambda x: x[1].find('.//a').attrib['href']
    ))
    field_loader.add_field(FieldToExtract(
        column='category_label',
        xpath='//li[@class="subcate"]',
        adjust_func=lambda x: x[1].find('.//a').text
    ))
    field_loader.add_field(FieldToExtract(
        column='date',
        xpath='',
        adjust_func=lambda x: str(datetime.date.today())  # function internally needs to have at
        # least 1 parameter, where selector is passed
    ))
    field_loader.add_field(FieldToExtract(
        column='price',
        xpath='.//span[@class="current-price"]',
        adjust_func=lambda x: x[0].text
    ))
    field_loader.add_field(FieldToExtract(
        column='old_price',
        xpath='.//span[@class="old-price"]',
        adjust_func=lambda x: x[0].text if x else None
    ))
    field_loader.add_field(FieldToExtract(
        column='good_name',
        xpath='.//div[@class="field-name"]/a',
        adjust_func=lambda x: x[0].text
    ))

    return field_loader


# UTILITY FUNCTIONS BLOCK

def create_file():
    with open(OUTPUT_CSV_PATH, 'w') as f:
        csv.writer(f).writerow(HEADERS)
        return OUTPUT_CSV_PATH


def write_row(df, _dict):
    if _dict['id'] not in df.index.values:
        id = _dict.pop('id')
        for key in _dict:
            df.loc[id, key] = _dict[key]
    else:
        pass


def configure_logging(logger_or_name=None, level=None, format=None):
    _format = format if format else LOG_FORMAT
    _level = level if level else LOG_LEVEL
    _name = logger_or_name if logger_or_name else __file__

    logger = logging.getLogger(_name)
    logger.setLevel(_level)
    if LOG_FILE:
        handler = logging.FileHandler(LOG_FILE)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=_format))
    logger.addHandler(handler)

    return logger


def zip_files(archive_name):
    # adds html files and output.csv to archive
    LOGGER.info('zipping files to %s.zip .....' % archive_name)
    file_list = [path.join(OUTPUT_HTML_PATH, html_file) for \
                 html_file in listdir(OUTPUT_HTML_PATH)]
    with zipfile.ZipFile(path.join(PROJECT_DIR, archive_name) + '.zip', 'w',
                         compression=zipfile.ZIP_DEFLATED) as myzip:
        for f in file_list:
            myzip.write(f, arcname=path.join(
                path.basename(path.dirname(f)), path.basename(f)))
        myzip.write(OUTPUT_CSV_PATH, arcname=path.basename(OUTPUT_CSV_PATH))
    LOGGER.info('zipped!')


# main

def main():
    DRIVER = CHROME_DRIVER
    FIELD_LOADER = declare_fields()
    OUTPUT_FILE = create_file()  # creates file and erases old 'output.csv'
    # get categories links
    categories = get_categories(DRIVER)
    LOGGER.info('category links scraped \n %s' % categories)
    for link in categories:
        # load each page for category
        for page_path in load_pages(DRIVER, link):
            # scrape_page function scrapes products from the whole page 1 by 1, and yields dict with values
            products = scrape_page(page_path, field_loader=FIELD_LOADER)
            products_counter = 0
            for product_dict in products:
                # write values to file
                products_counter += 1
                with open(OUTPUT_FILE, 'a') as f:
                    writer = csv.DictWriter(f, HEADERS)
                    writer.writerow(product_dict)
            LOGGER.info('%s products scraped for page %s' % (products_counter, page_path.split('/')[-1]))
    archive_filename = "lottevn_" + str(datetime.date.today())  # no need to add '.zip' it adds internally
    zip_files(archive_filename)


LOGGER = configure_logging(logger_or_name='main')

def daily_task():
    try:
        LOGGER.info('starting to scrape....')
        main()
        LOGGER.info('Finished!')
    except Exception as e:
        LOGGER.exception(e)
        raise e

if "test" in sys.argv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)