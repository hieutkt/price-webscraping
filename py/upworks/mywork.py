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
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import signal


SITE_NAME = "mywork"
BASE_URL = "https://mywork.com.vn"
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
            writer.writerow(('category', 'Salary', 'Work_location', 'Job_level', 'Industry', 'Job_type', 'Benefits', 'Gender', 'Experience', 'Education', 'Job_Description', 'Job_Requirement', 'date'))
        writer.writerow((data['category'], data['Salary'], data['Work_location'], data['Job_level'], data['Industry'], data['Job_type'], data['Benefits'], data['Gender'], data['Experience'], data['Education'], data['Job_Description'], data['Job_Requirement'], data['date']))

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
    browser2 = webdriver.Chrome(options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(options=chromeOptions)
    # browser2 = webdriver.Chrome()
    browser2.set_window_position(100, 40)
    browser2.set_window_size(1300, 1024)
    wait2 = ui.WebDriverWait(browser2,60)
    browser = webdriver.Chrome(options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser = webdriver.Chrome(options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    urls = []
    browser.get('https://mywork.com.vn/tuyen-dung')
    wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="__layout"]/section/section/div[1]/div[3]/div[1]/div[3]/div/div/div[1]'))
    soup = BeautifulSoup(browser.page_source, 'lxml')
    category_list = soup.find('div', class_='box-follow-category').find_all('div', class_='item')
    for item in category_list:
        url = BASE_URL + item.find('a').get('href')
        if url not in urls:
            urls.append(url)
    write_html(browser.page_source, "All_cat_")
    j=0
    while j < len(urls):
        browser.get(urls[j])
        wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="idJobNew"]/div[2]/section/ul'))
        soup = BeautifulSoup(browser.page_source, 'lxml')

        category = soup.find('ol', class_='breadcrumb').find('li', class_='active').text.strip()


        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="idJobNew"]/div[2]/section/ul'))
                    elements = browser.find_elements_by_css_selector('div#idJobNew ul.pagination > li')
                    # print(len(elements))
                    if len(elements) == 1:
                        pagination = False
                        break
                    c=0
                    while c < len(elements):
                        class_name = elements[c].get_attribute("class")
                        # print(class_name)
                        if "active" in class_name:
                            if len(elements)-1 >= c+1:
                                try:
                                    href_glob = elements[c+1].find_element_by_css_selector('a').get_attribute("href")
                                    browser.get(href_glob)
                                    c+=1
                                    break
                                except TimeoutException:
                                    pagination = False
                                    break
                                except:
                                    pagination = False
                                    break
                            else:
                                pagination = False
                                c+=1
                                break
                        c+=1
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', id='idJobNew').find_all('div', class_='job-over-item')
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
                # time.sleep(1)
                # wait.until(lambda browser: browser.find_element_by_xpath('//*[@id="idJobNew"]/div[2]/section/ul'))
            if i == 0:
                soup = BeautifulSoup(browser.page_source, 'lxml')
                list = soup.find('div', id='idJobNew').find_all('div', class_='job-over-item')
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                # if item.find('div', class_='ct_title') != None:
                #     title = item.find('div', class_='ct_title').text.strip()
                # else:
                #     title = None
                try:
                    href = BASE_URL + item.find('a').get('href')
                    browser2.get(href)
                    soup = BeautifulSoup(browser2.page_source, 'lxml')
                except TimeoutException:
                    continue
                except:
                    continue

                try:
                    if soup.find('div', id='detail-el').find('div', class_='col-md-7') != None:
                        Salary = soup.select('div#detail-el > div.row > div.col-md-7 > p')[1]
                        Salary = Salary.text.strip()
                        Salary = Salary.replace('Mức lương:','')
                        Salary = Salary.strip()
                    else:
                        Salary = None
                except:
                    Salary = None

                try:
                    if soup.find('div', id='detail-el').find('div', class_='col-md-7') != None:
                        Work_location = soup.find('div', id='detail-el').find('div', class_='col-md-7').find('p').text.strip()
                        Work_location = Work_location.replace('Địa điểm tuyển dụng:','')
                        Work_location = Work_location.strip()
                    else:
                        Work_location = None
                except:
                    Work_location = None

                try:
                    if soup.find('div', class_='job_detail_general').find('div', class_='item2') != None:
                        Job_level = soup.select('div.job_detail_general > div.item2 > p')[1]
                        Job_level = Job_level.text.strip()
                        Job_level = Job_level.replace('Chức vụ:','')
                        Job_level = Job_level.strip()
                    else:
                        Job_level = None
                except:
                    Job_level = None

                try:
                    if soup.find('div', id='detail-el').find('div', class_='col-md-7') != None:
                        Industry = soup.select('div#detail-el > div.row > div.col-md-7 > p')[0]
                        Industry = Industry.text.strip()
                        Industry = Industry.replace('Địa điểm tuyển dụng:','')
                        Industry = Industry.strip()
                    else:
                        Industry = None
                except:
                    Industry = None

                try:
                    if soup.find('div', class_='job_detail_general').find('div', class_='item2') != None:
                        Job_type = soup.select('div.job_detail_general > div.item2 > p')[0]
                        Job_type = Job_type.text.strip()
                        Job_type = Job_type.replace('Hình thức làm việc:','')
                        Job_type = Job_type.strip()
                    else:
                        Job_type = None
                except:
                    Job_type = None

                try:
                    if soup.find('div', class_='job_detail_general').find('div', class_='item2') != None:
                        Gender = soup.select('div.job_detail_general > div.item2 > p')[3]
                        Gender = Gender.text.strip()
                        Gender = Gender.replace('Yêu cầu giới tính:','')
                        Gender = Gender.strip()
                    else:
                        Gender = None
                except:
                    Gender = None

                try:
                    if soup.find('div', class_='job_detail_general').find('div', class_='item1') != None:
                        Experience = soup.select('div.job_detail_general > div.item1 > p')[0]
                        Experience = Experience.text.strip()
                        Experience = Experience.replace('Kinh nghiệm:','')
                        Experience = Experience.strip()
                    else:
                        Experience = None
                except:
                    Experience = None

                try:
                    if soup.find('div', class_='job_detail_general').find('div', class_='item1') != None:
                        Education = soup.select('div.job_detail_general > div.item1 > p')[1]
                        Education = Education.text.strip()
                        Education = Education.replace('Yêu cầu bằng cấp:','')
                        Education = Education.strip()
                    else:
                        Education = None
                except:
                    Education = None

                try:
                    if soup.find('div', class_='multiple').find('div', class_='mw-box-item') != None:
                        Job_Description = soup.select('div.multiple > div.mw-box-item')[2]
                        Job_Description = Job_Description.text.strip()
                        # Job_Description = Job_Description.replace('Yêu cầu bằng cấp:','')
                        # Job_Description = Job_Description.strip()
                    else:
                        Job_Description = None
                except:
                    Job_Description = None

                try:
                    if soup.find('div', class_='multiple').find('div', class_='mw-box-item') != None:
                        Job_Requirement = soup.select('div.multiple > div.mw-box-item')[4]
                        Job_Requirement = Job_Requirement.text.strip()
                        # Job_Requirement = Job_Requirement.replace('Yêu cầu bằng cấp:','')
                        # Job_Requirement = Job_Requirement.strip()
                    else:
                        Job_Requirement = None
                except:
                    Job_Requirement = None

                try:
                    if soup.find('div', class_='multiple').find('div', class_='mw-box-item') != None:
                        Benefits = soup.select('div.multiple > div.mw-box-item')[3]
                        Benefits = Benefits.text.strip()
                        Benefits = Benefits.replace('Yêu cầu bằng cấp:','')
                        Benefits = Benefits.strip()
                    else:
                        Benefits = None
                except:
                    Benefits = None

                # 5555555555---Salary, (shown as “Mức lương”)
                # 5555555555---Work location, (shown as “Địa điểm tuyển dụng”)
                # 5555555555---Job level, (shown as “Chức vụ”)
                # 5555555555---Industry, (shown as “Ngành nghề”)
                # 5555555555---Job type, (shown as “Hình thức làm việc”)
                # ---Age, (if exist)
                # 5555555555---Gender, (shown as “Yêu cầu giới tính”)
                # 5555555555---Experience, (shown as “Kinh nghiệm”)
                # 5555555555---Education, (shown as “Yêu cầu bằng cấp”)
                # 5555555555---Job Description, (shown as “Mô tả công việc”)
                # 5555555555---Job Requirement, (shown as “Yêu cầu công việc”)
                # 5555555555---Benefits, (shown as “Quyền lợi được hưởng”, if exists)
                # -5555555555--name of category
                # 555555555---current date

                data = {'category': category,
                        'Salary': Salary,
                        'Work_location': Work_location,
                        'Job_level': Job_level,
                        'Industry': Industry,
                        'Job_type': Job_type,
                        'Benefits': Benefits,
                        'Gender': Gender,
                        'Experience': Experience,
                        'Education': Education,
                        'Job_Description': Job_Description,
                        'Job_Requirement': Job_Requirement,
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
