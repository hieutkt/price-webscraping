#!/usr/bin/env python3
import schedule
"""Synch data from `data_dir` to `backup_dir`"""

import sys
import os
import datetime
import time


def sync_data(data_dir='csv/', backup_dir='backup_csv/'):
    """Synch data from `data_dir` to `backup_dir`"""
    sync_command = 'rsync -av ' + data_dir + ' ' + backup_dir
    os.system(sync_command)
    print('Finished synching data at: ' + str(datetime.datetime.now()))


if "test" in sys.argv:
    sync_data()
else:
    schedule.every().day.at("20:00").do(sync_data)
    while True:
        schedule.run_pending()
        time.sleep(1)
