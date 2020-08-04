import sys
import os
import csv
from zipfile import ZipFile
import time
import logging
import logging.handlers as handlers


def compress_csv():
    """Compress downloaded .csv files"""
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    os.chdir(csv_path)
    try:
        zip_csv = ZipFile(site_name + '_' + date + '_csv.zip', 'a')
        for file in glob.glob("*" + date + "*" + "csv"):
            zip_csv.write(file)
            os.remove(file)
        logging.info("Compressing %s item(s)", str(OBSERVATION))
    except Exception as e:
        logging.error('Error when compressing csv')
        logging.info(type(e).__name__ + str(e))
    os.chdir(project_path)

def compress_html():
    """Compress download .html files"""
    if not os.path.exists(html_path):
            os.makedirs(html_path)
    os.chdir(html_path)
    try:
        zip_csv = ZipFile(site_name + '_' + date + '_html.zip', 'a')
        for file in glob.glob("*" + date + "*" + "html"):
            zip_csv.write(file)
            os.remove(file)
        logging.info("Compressing HMTL files")
    except Exception as e:
        logging.error('Error when compressing html')
        logging.info(type(e).__name__ + str(e))
    os.chdir(project_path)
