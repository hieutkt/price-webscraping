from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
import zipfile
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains


SITE_NAME = "careerlink"
BASE_URL = "https://www.careerlink.vn"
PROJECT_PATH = re.sub("/py/.+", "", os.getcwd())
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CHROME_DRIVER_PATH = PROJECT_PATH + "/bin/chromedriver"

def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'Salary', 'Work_location', 'Job_level', 'Industry', 'Job_type', 'Age', 'Gender', 'Experience', 'Education', 'Job_Description', 'Job_Requirement', 'date'))
        writer.writerow((data['category'], data['Salary'], data['Work_location'], data['Job_level'], data['Industry'], data['Job_type'], data['Age'], data['Gender'], data['Experience'], data['Education'], data['Job_Description'], data['Job_Requirement'], data['date']))

def write_html(html, file_name):
    if not os.path.exists(PATH_HTML):
        os.makedirs(PATH_HTML)
    with open(PATH_HTML + file_name + SITE_NAME + "_" + DATE + ".html", 'a', encoding='utf-8-sig') as f:
        f.write(html)

def daily_task():
    global DATE
    DATE = str(datetime.date.today())
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images":2}
    # chromeOptions.add_argument("--disable-javascript")
    chromeOptions.add_argument("--headless")
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    urls = []
    browser.get('https://www.careerlink.vn/en')
    soup = BeautifulSoup(browser.page_source, 'lxml')
    category_list = soup.find('div', id='search-by-category').find_all('a')
    for item in category_list:
        url = BASE_URL + item.get('href')
        if url not in urls:
            urls.append(url)
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        browser.get(urls[j])
        wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/p'))
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category = soup.find('p', class_='lead-sm').find('strong').text.strip()
        category = category.replace('"', '')


        i=0
        pagination = True
        while pagination:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                if i == 1:
                    browser.get(urls[j])
                    file_name = str(j+1) + "_" + str(i) + "_"
                    write_html(browser.page_source, file_name)
                else:
                    browser.get(href_glob)
                    file_name = str(j+1) + "_" + str(i) + "_"
                    write_html(browser.page_source, file_name)
                wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[3]/nav/ul'))
                elements = browser.find_elements_by_css_selector('ul.pagination > li')
                if len(elements) == 1:
                    pagination = False
                    break
                c=0
                while c < len(elements):
                    class_name = elements[c].get_attribute("class")
                    if "active" in class_name:
                        if len(elements)-1 >= c+1:
                            href_glob = elements[c+1].find_element_by_css_selector('a').get_attribute("href")
                            browser.get(href_glob)
                            c+=1
                            break
                        else:
                            pagination = False
                            c+=1
                            break
                    c+=1
                wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[3]/nav/ul'))
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='list-group').find_all('div', class_='list-group-item')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='list-group').find_all('div', class_='list-group-item')
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # if item.find('div', class_='ct_title') != None:
                #     title = item.find('div', class_='ct_title').text.strip()
                # else:
                #     title = None
                href = BASE_URL + item.find('a').get('href')
                browser.get(href)
                wait.until(lambda browser: browser.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[1]'))
                soup = BeautifulSoup(browser.page_source, 'lxml')

                try:
                    if soup.find('span', itemprop='baseSalary') != None:
                        Salary = soup.find('span', itemprop='baseSalary').text.strip()
                    else:
                        Salary = None
                except:
                    Salary = None

                try:
                    if soup.find('span', itemprop='address') != None:
                        Work_location = soup.find('span', itemprop='address').text.strip()
                    else:
                        Work_location = None
                except:
                    Work_location = None

                try:
                    if soup.find('div', itemprop='skills') != None:
                        Job_Requirement = soup.find('div', itemprop='skills').text.strip()
                    else:
                        Job_Requirement = None
                except:
                    Job_Requirement = None

                try:
                    if soup.find('div', itemprop='description') != None:
                        Job_Description = soup.find('div', itemprop='description').text.strip()
                    else:
                        Job_Description = None
                except:
                    Job_Description = None

                # 5555555555 ---Salary,
                # 5555555555 ---Work location, (shown as “Work Location”)
                # ---Job level, (shown as “Career Level”)
                # ---Industry, (shown as “Job Category”)
                # ---Job type, (shown as “Position Type”)
                # ---Age, (shown as “Age”)
                # ---Gender, (shown as “Gender Require”)
                # ---Experience, (shown as “Experience Level”)
                # ---Education, (shown as “Education Level”)
                # 5555555555 ---Job Description, (shown as “Job Description Detail”)
                # 5555555555 ---Job Requirement, (shown as “Required Experience/Skills Detail)
                # ---Benefits, (if exists)

                Job_level = None
                Industry = None
                Job_type = None
                Age = None
                Gender = None
                Experience = None
                Education = None
                try:
                    ul = soup.select('div.job-data > ul.list-unstyled')[1]
                    lis = ul.find_all('li')
                    for li in lis:
                        txt = li.text.strip()
                        if "Career Level" in txt:
                            Job_level = txt
                            # Job_level = li.text.strip()
                            Job_level = Job_level.replace('Career Level:','')
                            Job_level = Job_level.strip()
                            continue
                        if "Job Category" in txt:
                            Industry = txt
                            # Industry = li.text.strip()
                            Industry = Industry.replace('Job Category:','')
                            Industry = Industry.strip()
                            continue
                        if "Position Type" in txt:
                            Job_type = txt
                            # Job_type = li.text.strip()
                            Job_type = Job_type.replace('Position Type:','')
                            Job_type = Job_type.strip()
                            continue
                        if "Age" in txt:
                            Age = txt
                            # Age = li.text.strip()
                            Age = Age.replace('Age:','')
                            Age = Age.strip()
                            continue
                        if "Gender Require" in txt:
                            Gender = txt
                            # Gender = li.text.strip()
                            Gender = Gender.replace('Gender Require:','')
                            Gender = Gender.strip()
                            continue
                        if "Experience Level" in txt:
                            Experience = txt
                            # Experience = li.text.strip()
                            Experience = Experience.replace('Experience Level:','')
                            Experience = Experience.strip()
                            continue
                        if "Education Level" in txt:
                            Education = txt
                            # Education = li.text.strip()
                            Education = Education.replace('Education Level:','')
                            Education = Education.strip()
                            continue
                except:
                    Job_level = None
                    Industry = None
                    Job_type = None
                    Age = None
                    Gender = None
                    Experience = None
                    Education = None

                
                data = {'category': category,
                        'Salary': Salary,
                        'Work_location': Work_location,
                        'Job_level': Job_level,
                        'Industry': Industry,
                        'Job_type': Job_type,
                        'Age': Age,
                        'Gender': Gender,
                        'Experience': Experience,
                        'Education': Education,
                        'Job_Description': Job_Description,
                        'Job_Requirement': Job_Requirement,
                        'date': DATE}
                write_csv(data)
            # file_name = str(j+1) + "_" + str(i+1) + "_"
            # write_html(browser.page_source, file_name)
            i+=1
        j+=1
    browser.quit()
    compress_data()

def compress_data():
    """Compress downloaded .csv and .html files"""
    os.chdir(PATH_CSV)
    z = zipfile.ZipFile(SITE_NAME + "_" + DATE + "_csv.zip", "a")
    z.write(SITE_NAME + "_" + DATE + ".csv")
    os.remove(SITE_NAME + "_" + DATE + ".csv")

    os.chdir(PATH_HTML)
    z = zipfile.ZipFile(SITE_NAME + "_" + DATE + "_html.zip", "a")
    for file in glob.glob("*.html"):
        z.write(file)
        os.remove(file)

if "test" in sys.argv:
    daily_task()
else:
    schedule.every().day.at("06:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
