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
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select



SITE_NAME = "laodong"
BASE_URL = "http://vieclam.laodong.com.vn"
PROJECT_PATH = os.getcwd()
PROJECT_PATH = PROJECT_PATH.replace("\\",'/')
PATH_HTML = PROJECT_PATH + "/html/" + SITE_NAME + "/"
PATH_CSV = PROJECT_PATH + "/csv/" + SITE_NAME + "/"
CHROME_DRIVER_PATH = "bin/chromedriver"

def write_csv(data):
    file_exists = os.path.isfile(PATH_CSV + SITE_NAME + "_" + DATE + ".csv")
    if not os.path.exists(PATH_CSV):
        os.makedirs(PATH_CSV)
    with open(PATH_CSV + SITE_NAME + "_" + DATE + ".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=',')
        if not file_exists:
            writer.writerow(('category', 'Salary', 'Min_Salary', 'Max_Salary', 'Work_location', 'Job_level', 'Industry', 'Age', 'Gender', 'Education', 'Experience', 'Job_Description', 'Job_Requirement', 'Benefits', 'date'))
        writer.writerow((data['category'], data['Salary'], data['Min_Salary'], data['Max_Salary'], data['Work_location'], data['Job_level'], data['Industry'],data['Age'], data['Gender'], data['Education'], data['Experience'], data['Job_Description'], data['Job_Requirement'],data['Benefits'], data['date']))


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
    chromeOptions.add_argument("--headless")
    chromeOptions.add_experimental_option("prefs",prefs)
    browser2 = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    browser = webdriver.Chrome(chrome_options=chromeOptions,executable_path=CHROME_DRIVER_PATH)
    # browser2 = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome(chrome_options=chromeOptions)
    # browser = webdriver.Chrome()
    browser.set_window_position(400, 40)
    browser.set_window_size(1300, 1024)
    wait = ui.WebDriverWait(browser,60)
    wait2 = ui.WebDriverWait(browser,10)
    urls = []
    browser.get(BASE_URL)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    uls = soup.find('div', id='alphabet-sort').find_all('ul', class_='col')
    for ul in uls:
        lis = ul.find_all('li')
        for li in lis:
            url = BASE_URL + li.find('a').get('href')
            if url not in urls:
                urls.append(url)
    j=0
    write_html(browser.page_source, "All_cat_")
    while j < len(urls):
        browser.get(urls[j])

        wait.until(lambda browser: browser.find_element_by_css_selector('#form1 > main > div.site-wrap > div:nth-child(1) > section > div > div.normal-news > header > h3'))
        category = browser.find_element_by_css_selector('#form1 > main > div.site-wrap > div:nth-child(1) > section > div > div.normal-news > header > h3').text.replace('"', '').strip()

        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('#cphMainContent_pager > ul'))
                    elements = browser.find_elements_by_css_selector('#cphMainContent_pager > ul > li')
                    c=0
                    while c < len(elements)-1:
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-2 >= c+1:
                                href_glob = elements[c+1].find_element_by_css_selector('a').get_attribute("href")
                                browser.get(href_glob)
                                c+=1
                                break
                            else:
                                pagination = False
                                c+=1
                                break
                        c+=1
                except NoSuchElementException:
                    pagination = False
                except TimeoutException:
                    pagination = False
                except:
                    pagination = False
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='normal-news').find_all('article', class_='hot-news')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='normal-news').find_all('article', class_='hot-news')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                if item.find('h3', class_='name').find('a') == None:
                    continue
                else:
                    href = BASE_URL + item.find('h3', class_='name').find('a').get('href')
                    try:
                        browser2.get(href)
                    except TimeoutException:
                        continue
                
                soup = BeautifulSoup(browser2.page_source, 'lxml')
                

                # ---11111111111111111111111111111111111111111Salary, (shown as “Mức lương”)
                # ---11111111111111111111111111111111111111111Min Salary, (shown as “Mức lương tối thiểu”, if exist)
                # ---11111111111111111111111111111111111111111Max Salary, (shown as “Mức lương tối đa”, if exist)
                # ---11111111111111111111111111111111111111111Work location, (shown as “Địa điểm làm việc”)
                # ---11111111111111111111111111111111111111111Job level, (shown as “Cấp bậc”)
                # ---11111111111111111111111111111111111111111Industry, (shown as “Ngành nghề”)
                # ---1111111111111111111111111111111111111111Age, (shown as “Độ tuổi”)
                # ---1111111111111111111111111111111111111111Gender, (shown as “Giới tính”)
                # ---1111111111111111111111111111111111111111Education, (shown as “Trình độ”)
                # ---1111111111111111111111111111111111111111Experience, (shown as “Kinh nghiệm”)
                # ---111111111111111111111111111111111111111Job Description, (shown as “Mô tả công việc”)
                # ---111111111111111111111111111111111111111Job Requirement, (shown as “Yêu cầu công việc")
                # ---1111111111111111111111111111111111111111Benefits, (also shown as “Chế độ quyền lợi khác”, if exist)
                # ---1111111111111111111111111111111111111111name of category
                # ---11111111111111111111111111111111111111111current date

                try:
                    Salary = soup.find('div', id='cphMainContent_pnNegotiableSalary').find('span', class_='pull-right').text.strip()
                except:
                    Salary = None

                try:
                    if soup.find('span', id='cphMainContent_lblMaxAge').text.strip() != "":
                        Age = soup.find('span', id='cphMainContent_lblMinAge').text.strip() + " - " + soup.find('span', id='cphMainContent_lblMaxAge').text.strip()
                    else:
                        Age = soup.find('span', id='cphMainContent_lblMinAge').text.strip()
                except:
                    Age = None

                try:
                    Benefits = soup.find('span', id='cphMainContent_lblOtherAdvanced').text.strip()
                except:
                    Benefits = None

                try:
                    Job_Requirement = soup.find('span', id='cphMainContent_lblRequirements').text.strip()
                except:
                    Job_Requirement = None

                try:
                    Job_Description = soup.find('span', id='cphMainContent_lblDescription').text.strip()
                except:
                    Job_Description = None

                try:
                    Experience = soup.find('span', id='cphMainContent_lblExperienceRequired').text.strip()
                except:
                    Experience = None

                try:
                    Education = soup.find('span', id='cphMainContent_lblEducationLevelIDRequired').text.strip()
                except:
                    Education = None

                try:
                    Industry = soup.find('span', id='cphMainContent_lblJobCategoryID').text.strip()
                except:
                    Industry = None

                try:
                    Gender = soup.find('span', id='cphMainContent_lblGenderRequired').text.strip()
                except:
                    Gender = None

                try:
                    Work_location = soup.find('span', id='cphMainContent_lblWorkLocationID').text.strip()
                except:
                    Work_location = None

                try:
                    Job_level = soup.find('span', id='cphMainContent_lblJobLevelID').text.strip()
                except:
                    Job_level = None

                try:
                    Min_Salary = soup.find('div', id='cphMainContent_pnFixedSalary').find('span', class_='pull-right').text.strip()
                except:
                    Min_Salary = None

                try:
                    Max_Salary = soup.select('#cphMainContent_pnFixedSalary > p')[1]
                    Max_Salary = Max_Salary.find('span', class_='pull-right').text.strip()
                except:
                    Max_Salary = None


                data = {'category': category,
                        'Salary': Salary,
                        'Min_Salary': Min_Salary,
                        'Max_Salary': Max_Salary,
                        'Work_location': Work_location,
                        'Job_level': Job_level,
                        'Industry': Industry,
                        'Age': Age,
                        'Gender': Gender,
                        'Education': Education,
                        'Experience': Experience,
                        'Job_Description': Job_Description,
                        'Job_Requirement': Job_Requirement,
                        'Benefits': Benefits,
                        'date': DATE}
                write_csv(data)
            file_name = str(j+1) + "_" + str(i+1) + "_"
            write_html(browser.page_source, file_name)
            i+=1
        # print(j)
        j+=1
    browser.quit()
    browser2.quit()
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
