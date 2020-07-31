#!/usr/bin/env python3
"""This script create a PriceScraper object that streamline
scraping interactions"""

from selenium.webdriver.chrome.webdriver import WebDriver
import loggings_setup


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
        loggings_setup.setup_loggings(self.log_path, self.site_name)

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
