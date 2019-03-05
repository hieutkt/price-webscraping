from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import time
import csv
import sys
import glob, os
import re
import schedule
import random
import zipfile
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
import signal


SITE_NAME = "viectotnhat"
BASE_URL = "https://viectotnhat.com"
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
            writer.writerow(('category', 'Salary', 'Work_location', 'Job_level', 'Industry', 'Job_type', 'Gender', 'Education', 'Experience', 'Job_Description', 'Job_Requirement', 'Benefits', 'date'))
        writer.writerow((data['category'], data['Salary'], data['Work_location'], data['Job_level'], data['Industry'],data['Job_type'], data['Gender'], data['Education'], data['Experience'], data['Job_Description'], data['Job_Requirement'],data['Benefits'], data['date']))


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
    chromeOptions.add_experimental_option("prefs",prefs)
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("start-maximized")
    chromeOptions.add_argument("disable-infobars")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--no-sandbox")
    chromeOptions.add_argument("--disable-dev-shm-usage")
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
    browser.get('https://viectotnhat.com/viec-lam/danh-sach-nganh')
    soup = BeautifulSoup(browser.page_source, 'lxml')
    uls = soup.find('ul', class_='list-tinh-thanh').find_all('li')
    for ul in uls:
        url = ul.find('a').get('href')
        if url not in urls:
            urls.append(url)
    j=0
    write_html(browser.page_source, "All_cat_")
    while j < len(urls):
        sys.stdout.write('\rScraping ' + urls[j] + ' ...' + ' '*10)
        browser.get(urls[j])
        try:
            wait.until(lambda browser: browser.find_element_by_css_selector('#main-content > div > div > div > div.col-xs-12.col-sm-8.col-md-8.col-lg-8.padding0.w67p.marginBottom30.marginBottom10-mb > h2 > span:nth-child(2)'))
            category = browser.find_element_by_css_selector('#main-content > div > div > div > div.col-xs-12.col-sm-8.col-md-8.col-lg-8.padding0.w67p.marginBottom30.marginBottom10-mb > h2 > span:nth-child(2)').text.replace('"', '').strip()
        except TimeoutException:
            j+=1
            continue
        i=0
        pagination = True
        while pagination:
            if i != 0:
                try:
                    wait.until(lambda browser: browser.find_element_by_css_selector('ul.pagination'))
                    elements = browser.find_elements_by_css_selector('ul.pagination a')
                    c=0
                    while c < len(elements)-1:
                        class_name = elements[c].get_attribute("class")
                        if "active" in class_name:
                            if len(elements)-2 >= c+1:
                                # href_glob = elements[c+1].get_attribute("href")
                                browser.get(urls[j] + '?page=' + str(i+1))
                                # browser.execute_script("arguments[0].click();", elements[c+1])
                                # wait.until(lambda browser: browser.find_element_by_css_selector('#main-content > div > div > div > div.col-xs-12.col-sm-8.col-md-8.col-lg-8.padding0.w67p.marginBottom30.marginBottom10-mb > div.alignCenter.marginBottom10.hidden-xs > nav > ul'))
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
                    list = soup.find('div', class_='normal-job').find_all('div', class_='tr-box')
                except:
                    pagination = False
            if i == 0:
                try:
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    list = soup.find('div', class_='normal-job').find_all('div', class_='tr-box')
                except:
                    pagination = False
            if pagination == False:
                break
            # print(len(list))
            # print(i+1)
            for item in list:
                try:
                    if item.find('h3', class_='job-name').find('a') == None:
                        continue
                except:
                    continue
                href = item.find('h3', class_='job-name').find('a').get('href')
                try:
                    browser2.get(href)
                except TimeoutException:
                    continue

                soup = BeautifulSoup(browser2.page_source, 'lxml')


                # ---1111111111111111111111111111111111111Salary, (shown as “Mức lương”)
                # ---111111111111111111111111111111111111Work location, (shown as “Địa điểm làm việc”)
                # ---111111111111111111111111111111111111Job level, (shown as “Chức vụ”)
                # ---11111111111111111111111111111111111Industry, (shown as “Ngành nghề”)
                # ---11111111111111111111111111111111111Job type, (shown as “Hình thức làm việc”)
                # ---11111111111111111111111111111111111Gender, (shown as “Yêu cầu giới tính”)
                # ---11111111111111111111111111111111111Education, (shown as “Yêu cầu bằng cấp”)
                # ---11111111111111111111111111111111111Experience, (shown as “Kinh nghiệm”)
                # ---11111111111111111111111111111111111Job Description, (shown as “Mô tả công việc”)
                # ---1111111111111111111111111111111111Job Requirement, (shown as “Yêu cầu công việc")
                # ---1111111111111111111111111111111111111Benefits, (also shown as “Quyền lợi”, if exist)
                # ---111111111111111111111111111111111111111name of category
                # ---111111111111111111111111111111111111111current date

                Salary = None
                Work_location = None
                Job_level = None
                Industry = None
                Job_type = None
                Gender = None
                Education = None
                Experience = None
                try:
                    lis = soup.find('div', class_='list-thong-tin').find('ul').find_all('li')
                    for li in lis:
                        txt = li.text.strip()
                        if "Mức lương" in txt:
                            Salary = txt.replace('"', '').replace('Mức lương:', '').strip()
                        if "Địa điểm làm việc" in txt:
                            Work_location = txt.replace('"', '').replace('Địa điểm làm việc:', '').strip()
                        if "Chức vụ" in txt:
                            Job_level = txt.replace('"', '').replace('Chức vụ:', '').strip()
                        if "Ngành nghề" in txt:
                            Industry = txt.replace('"', '').replace('Ngành nghề:', '').strip()
                        if "Hình thức làm việc" in txt:
                            Job_type = txt.replace('"', '').replace('Hình thức làm việc:', '').strip()
                        if "Yêu cầu giới tính" in txt:
                            Gender = txt.replace('"', '').replace('Yêu cầu giới tính:', '').strip()
                        if "Yêu cầu bằng cấp" in txt:
                            Education = txt.replace('"', '').replace('Yêu cầu bằng cấp:', '').strip()
                        if "Kinh nghiệm" in txt:
                            Experience = txt.replace('"', '').replace('Kinh nghiệm:', '').strip()
                except:
                    s = 0

                try:
                    Benefits = soup.find('div', class_='quyen-loi').text.strip()
                except:
                    Benefits = None

                try:
                    Job_Requirement = soup.find('div', class_='yeu-cau').text.strip()
                except:
                    Job_Requirement = None

                try:
                    Job_Description = soup.find('div', class_='mo-ta-cv').text.strip()
                except:
                    Job_Description = None


                data = {'category': category,
                        'Salary': Salary,
                        'Work_location': Work_location,
                        'Job_level': Job_level,
                        'Industry': Industry,
                        'Job_type': Job_type,
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
    # Close browser
    browser.close()
    browser.service.process.send_signal(signal.SIGTERM)
    browser.quit()
    # Close browser
    browser2.close()
    browser2.service.process.send_signal(signal.SIGTERM)
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
    start_time = '01:' + str(random.randint(0,59)).zfill(2)
    schedule.every().day.at(start_time).do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == '__main__':
#     daily_task()
