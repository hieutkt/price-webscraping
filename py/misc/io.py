import os
import datetime
import time
import csv

def write_data(item_data):

    fieldnames = ['good_name', 'price', 'old_price', 'id', 'category', 'category_label', 'date']
    file_exist = os.path.isfile(csv_path + site_name + "_" + date + ".csv")
if not os.path.exists(csv_path):
    os.makedirs(csv_path)
with open(csv_path + site_name + "_" + date + ".csv", "a") as f:
    writer = csv.DictWriter(f, fieldnames)
    if not file_exists: 
        writer.writehearder()
    writer.writerow(item_data)
