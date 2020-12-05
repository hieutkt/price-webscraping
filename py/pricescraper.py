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
from py.misc.loggings_setup import setup_loggings
from py.misc.compress import Compressor


class PriceScraper():
    """Scraper object to scrape prices from online retailers"""

    driverpath = "./bin/chromedriver"
    log_path = "./log"

    def __init__(self, base_url, site_name, project_path,log_path=log_path):
        self.observation = 0
        self.driver = WebDriver()
        self.base_url = base_url
        self.cat_list = []
        self.log_path = log_path
        self.site_name = site_name
        self.project_path = project_path

    def setup_loggings(self):
        """Setting up loggings"""
        setup_loggings(self.log_path, self.site_name)

    def main(self):
        """Deploy the scraper to scrap data automatically"""
        # Find all category pages
        # For all item on each category pages and write data into CSVs
        # Compress the remains CSVs and HTMLs
        compressor = Compressor(site_name=self.site_name,
                                project_path=self.project_path,
                                observation=self.observation)
        compressor.compress_csv()
        compressor.compress_html()
