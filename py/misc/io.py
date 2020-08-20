import os
import datetime
import time
import csv

class Output:
    def __init__(self, good_name, price, old_price, id, category, category_label, date = str(datetime.date.today())):
       self.good_name = good_name
       self.price = price
       self.old_price = old_price
       self.id = id
       self.category = category
       self.category_label = category_label
       self.date = date

    def write_data(item_data):
        fieldnames = [self.good_name, self.price, self.old_price, self.id, self.category, self.category_label, self.date]
        file_exist = os.path.isfile(csv_path + site_name + "_" + date + ".csv")
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    with open(csv_path + site_name + "_" + date + ".csv", "a") as f:
        writer = csv.DictWriter(f, fieldnames)
        if not file_exists: 
            writer.writehearder()
        writer.writerow(item_data)

    coloredlogs.install()