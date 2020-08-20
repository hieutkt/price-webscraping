import sys
import os
import csv
from zipfile import ZipFile
import time
import datetime
from misc.loggings_setup import setup_loggings

class Compressor:
    def __init__(self, csv_path, html_path, observation, date = str(datetime.date.today())):
        self.csv_path = csv_path
        self.html_path = html_path
        self.obervation = 0 
        self.date = date
    
    def compress_csv():
        """Compress downloaded .csv files"""
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)
        os.chdir(self.csv_path)
        try:
            zip_csv = ZipFile(self.site_name + '_' + self.date + '_csv.zip', 'a')
            for file in glob.glob("*" + self.date + "*" + "csv"):
                zip_csv.write(file)
                os.remove(file)
            logging.info("Compressing %s item(s)", str(self.observation)
        except Exception as e:
            logging.error('Error when compressing csv')
            logging.info(type(e).__name__ + str(e))
        os.chdir(self.project_path)

    def compress_html():
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

