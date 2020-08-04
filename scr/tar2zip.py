"""Re-compress all tar.gz into zip files"""

import os
from zipfile import ZipFile

CURRENT_PATH = os.getcwd()

list_folders = os.listdir()

for folder in list_folders:
    print("Entering: " + folder)
    os.chdir(folder)
    # List all tar and un archive
    list_files = os.listdir()
    print("Find " + str(len(list_files)) + " files")
    for file_ in list_files:
        if file_.endswith("tar.gz"):
            print(file_, " Decompressing tar...")
            untar_cmd = "tar -xzf " + file_ + " && rm " + file_
            os.system(untar_cmd)
    # compress all csv
    list_files = os.listdir()
    for file_ in list_files:
        if file_.endswith("csv"):
            print(file_, " Compressing into zip")
            z_csv = ZipFile(file_[:-4] + "_csv.zip", "a")
            z_csv.write(file_)
            os.remove(file_)
    # Return to the original folder
    os.chdir(CURRENT_PATH)
