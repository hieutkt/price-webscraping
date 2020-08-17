#!/usr/bin/env python3
"""This script create a PriceScraper object that streamline
scraping interactions

  Typical usage example:

  from pricescraper import PriceScraper
  from categories.nested_cat import NestedCat
  from items.indentify import ItemIdentify
  from blocked_data.pagination import Pagination

  PriceScraper.site_name = "lazada"
  PriceScraper.base_url = "lazada.vn"
  PriceScraper.category_identificator = NestedCat("<xpath-selector>")
  PriceScraper.item_identificator = ItemIndentify("...")
  PriceScraper.blocked_method = Pagination("...")

  PriceScraper.deploy()
"""

from selenium.webdriver.chrome.webdriver import WebDriver
from misc.loggings_setup import setup_loggings


class PriceScraper():
    """Scraper object to scrape prices from online retailers"""

    driverpath = "./bin/chromedriver"
    log_path = "./log"

    def __init__(self, base_url, site_name, log_path=log_path):
        self.driver = WebDriver()
        self.base_url = base_url
        self.cat_list = []
        self.log_path = log_path
        self.site_name = site_name

    def setup_loggings(self):
        """Setting up loggings"""
        setup_loggings(self.log_path, self.site_name)

    def get_source(self):
        """Get the html source of the driver"""
        return self.driver.page_source()

    def get_category_list(self):
        """Return the lists of category"""

    def get_data(self):
        """Scrap data from individual category"""

    def compress_data(self):
        """Compress data"""

    def compress_source(self):
        """Compress html"""
