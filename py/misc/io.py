#!/usr/bin/env python3
"""Write collected data into CSVs"""

import os
import csv

def write_data(item_data, csv_path, site_name, date):
    """Write collected data into csv"""
    fieldnames = item_data.keys()
    file_exists = os.path.isfile(csv_path + site_name + "_" + date + ".csv")
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    with open(csv_path + site_name + "_" + date + ".csv", "a") as f:
        writer = csv.DictWriter(f, fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(item_data)
