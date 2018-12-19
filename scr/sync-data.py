import schedule
import sys
import os
import datetime
import time


def sync_data():
    sync_command = 'rsync -av  csv/ backup_csv/'
    os.system(sync_command)
    print('Finished synching data at: ' + str(datetime.datetime.now()))

if "test" in sys.argv:
    sync_data()
else:
    schedule.every().monday.at("05:30").do(sync_data)
    while True:
        schedule.run_pending()
        time.sleep(1)
