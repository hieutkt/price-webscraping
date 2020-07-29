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
import random
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import signal


SITE_NAME = "careerbuilder"
BASE_URL = "https://careerbuilder.vn"
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
            writer.writerow(('category', 'Salary', 'Work_location', 'Job_level', 'Industry', 'Job_type', 'Age', 'Gender', 'Experience', 'Education', 'Job_Description', 'Job_Requirement', 'Benefits', 'date'))
        writer.writerow((data['category'], data['Salary'], data['Work_location'], data['Job_level'], data['Industry'], data['Job_type'], data['Age'], data['Gender'], data['Experience'], data['Education'], data['Job_Description'], data['Job_Requirement'], data['Benefits'], data['date']))

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
    chromeOptions.add_experimental_option("prefs",prefs)
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument("disable-infobars")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
    # PROXY = "212.34.52.43:8080" # IP:PORT or HOST:PORT
    # chromeOptions.add_argument('--proxy-server=http://%s' % PROXY)
    browser2 = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(chrome_options=chromeOptions)
    # browser2 = webdriver.Chrome()
    browser2.set_window_position(100, 40)
    browser2.set_window_size(1300, 1024)
    wait2 = ui.WebDriverWait(browser2,60)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    browser.get('https://careerbuilder.vn/search-job.html')
    urls = []
    titles = []
    soup = BeautifulSoup(browser.page_source, 'lxml')
    category_list = soup.find('div', id='JobCategoriesListing').find_all('a')
    for item in category_list:
        url = item.get('href')
        title = item.text.strip()
        if url not in urls:
            urls.append(url)
            titles.append(title)
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        sys.stdout.write('Scraping ' + urls[j] + ' ...' + ' '*10)
        browser.get(urls[j])
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category = titles[j]

        i=0
        pagination = True
        while pagination:
            soup = BeautifulSoup(browser.page_source, 'lxml')
            if i != 0:
                try:
                    element = browser.find_element_by_css_selector('a.right')
                    if element.is_displayed():
                        browser.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                    else:
                        pagination = False
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='col-ListJobCate').find_all('dd', class_='brief')
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', class_='col-ListJobCate').find_all('dd', class_='brief')
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # if item.find('div', class_='ct_title') != None:
                #     title = item.find('div', class_='ct_title').text.strip()
                # else:
                #     title = None
                href = item.find('h3', class_='job').find('a').get('href')
                browser2.get(href)
                soup = BeautifulSoup(browser2.page_source, 'lxml')

                if soup.find('div', class_='MyJobDetail') != None:
                    Salary = None
                    Work_location = None
                    Job_level = None
                    Industry = None
                    Experience = None
                    try:
                        lis = soup.find('ul', class_='DetailJobNew').find_all('li')
                        for li in lis:
                            ps = li.find_all('p')
                            for p in ps:
                                txt = p.text.strip()
                                if "Salary" in txt:
                                    Salary = txt
                                    Salary = Salary.replace('Salary:','')
                                    Salary = Salary.strip()
                                    continue
                                if "Work location" in txt:
                                    Work_location = txt
                                    Work_location = Work_location.replace('Work location:','')
                                    Work_location = Work_location.strip()
                                    continue
                                if "Job level" in txt:
                                    Job_level = txt
                                    Job_level = Job_level.replace('Job level:','')
                                    Job_level = Job_level.strip()
                                    continue
                                if "Industry" in txt:
                                    Industry = txt
                                    Industry = Industry.replace('Industry:','')
                                    Industry = Industry.strip()
                                    continue
                                if "Experience" in txt:
                                    Experience = txt
                                    Experience = Experience.replace('Experience:','')
                                    Experience = Experience.strip()
                                    continue
                    except:
                        c = 0

                    Benefits = None
                    try:
                        lis = soup.find('ul', class_='list-benefits').find_all('li')
                        for li in lis:
                            txt = li.text.strip()
                            Benefits = Benefits + txt + ",\n"
                    except:
                        c = 0

                    Job_Requirement = None
                    Job_Description = None
                    Job_type = None
                    Age = None
                    Gender = None
                    Education = None
                    try:
                        blocks = soup.find('div', class_='LeftJobCB').find_all('div', class_='MarBot20')
                        for block in blocks:
                            txt = block.find('h4').text.strip()
                            if "Job Requirement" in txt:
                                Job_Requirement = block.find('div', class_='content_fck').text.strip()
                                continue
                            if "Job Description" in txt:
                                Job_Description = block.find('div', class_='content_fck').text.strip()
                                continue
                            if "More Information" in txt:
                                lis = block.find('ul').find_all('li')
                                for li in lis:
                                    text_li = li.text.strip()
                                    if "Job type" in text_li:
                                        Job_type = text_li
                                        Job_type = Job_type.replace('Job type:','')
                                        Job_type = Job_type.strip()
                                        continue
                                    if "Age" in text_li:
                                        Age = text_li
                                        Age = Age.replace('Age:','')
                                        Age = Age.strip()
                                        continue
                                    if "Gender" in text_li:
                                        Gender = text_li
                                        Gender = Gender.replace('Gender:','')
                                        Gender = Gender.strip()
                                        continue
                                    if "Degree" in text_li:
                                        Education = text_li
                                        Education = Education.replace('Degree:','')
                                        Education = Education.strip()
                                        continue
                    except:
                        c = 0
                else:
                    continue

                # 555555555555---Salary,
                # 555555555555---Work location, (shown as “Work location”)
                # 555555555555---Job level, (shown as “Job level”)
                # 555555555555---Industry, (shown as “Industry”)
                # ---Job type, (shown as “Job type”)
                # ---Age, (if exist)
                # ---Gender, (if exist)
                # 55555555---Experience, (if exist)LeftJobCB
                # ---Education, (if exist)
                # 555555555---Job Description, (shown as “Job Description”)
                # 655555555---Job Requirement, (shown as “Job Requirement")
                # 5555555555555---Benefits, (also shown as “Quyền lợi”, if exist)
                # 555555555555555555555---name of category
                # 55555555555555555---current date


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
                        'Benefits': Benefits,
                        'date': DATE}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            i+=1
        j+=1
    # Close browser
    browser.close()
    browser.service.process.send_signal(signal.SIGTERM)
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
