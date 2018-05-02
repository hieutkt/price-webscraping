import re
import os


def clone_py2(py_file):
    with open(py_file, "r") as f:
        contents = f.read()
        contents = contents.split("\n")
        contents = [re.sub("import csv", "import unicodecsv as csv", i)
                    for i in contents]
        contents = [re.sub("from urllib.request", "from urllib", i)
                    for i in contents]
        print_index = [i for i, word in enumerate(contents) if
                       re.match(".+print.+", word)]
        print_fix = [re.sub(",", " + ", re.sub("[\(\)]", " ", contents[i]))
                     for i in print_index]
        for i, v in enumerate(print_index):
            contents[v] = print_fix[i]
            os.makedirs(os.getcwd() + "/py2/", exist_ok=True)
            with open(os.getcwd() + "/py2/py2_" + py_file, "w") as w:
                for line in contents:
                    w.write("%s\n" % line)

                    
py_files = list(filter(lambda x: x.startswith("prices"), os.listdir()))

for py_file in py_files:
    clone_py2(py_file)
