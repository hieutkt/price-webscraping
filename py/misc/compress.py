#!/usr/bin/env python3
"""Compressor class for dealing with CSVs and HTMLs"""

import os
from zipfile import ZipFile
import glob
import datetime
import logging


class Compressor:
    def __init__(self, project_path, site_name, observation, date=str(datetime.date.today())):
        self.project_path = project_path
        self.csv_path = project_path + "/csv/"
        self.html_path = project_path + "/html/"
        self.obervation = 0
        self.date = date
        self.site_name = site_name
        self.observation = observation

    def compress_csv(self):
        """Compress downloaded .csv files"""
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)
        os.chdir(self.csv_path)
        try:
            zip_csv = ZipFile(self.site_name + '_' + self.date + '_csv.zip', 'a')
            for file in glob.glob("*" + self.date + "*" + "csv"):
                zip_csv.write(file)
                os.remove(file)
            logging.info("Compressing %s item(s)", str(self.observation))
        except Exception as e:
            logging.error('Error when compressing csv')
            logging.info(type(e).__name__ + str(e))
        os.chdir(self.project_path)

    def compress_html(self):
        """Compress download .html files"""
        if not os.path.exists(self.html_path):
                os.makedirs(self.html_path)
        os.chdir(self.html_path)
        try:
            zip_csv = ZipFile(self.site_name + '_' + self.date + '_html.zip', 'a')
            for file in glob.glob("*" + self.date + "*" + "html"):
                zip_csv.write(file)
                os.remove(file)
            logging.info("Compressing HMTL files")
        except Exception as e:
            logging.error('Error when compressing html')
            logging.info(type(e).__name__ + str(e))
        os.chdir(self.project_path)
