#-*- coding: utf8 -*-
# Created by qjy on 2018/8/23 0023
import datetime,time,json,os,threading,redis,traceback
from lxml import etree
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.touch_actions import TouchActions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def clear_data(list_time,list_content):
    '''
    对爬取数据进行过滤（1.时间上午处理，2.包含特殊换行符等转义过滤）
    :param list_time:
    :param list_content:
    :return:
    '''
    commtent_time = []
    commtent_name = []
    for li in list_time:
        try:
            li = (datetime.datetime.strptime(li.text.strip(), "%I:%M %p")).strftime('%H:%M')
        except:
            li = (datetime.datetime.strptime(li.text.strip(), "%H:%M %p")).strftime('%H:%M')
        commtent_time.append(li)

    for li in list_content:
        commtent_name.append(li.text.strip().replace("\"", "").replace("'", "\'"))
    return commtent_time,commtent_name

def get_data():
    options = Options()
    # 设置成手机模式
    mobile_emulation = {"deviceName": "iPhone 6"}
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    #关闭浏览器提示框
    options.add_argument('disable-infobars')
    #设置无界面模式
    # options.add_argument('headless')
    driver = webdriver.Chrome(chrome_options=options)

    basepath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #获取xml文件中的配置
    confpath = os.path.join(basepath,"Seleun","epg_config_india.xml")
    with open(confpath) as f:
        cnf = f.read()
    root = etree.XML(cnf)
    spdernode = root.xpath("//APK_TYPE[@lan='%s']" % "India")[0]

    programs = spdernode.xpath("./channel")
    try:
        for pg in programs:
            #获取需要爬取的频道
            db_id = pg.xpath("./key/text()")[0]
            name = pg.xpath("./name/text()")[0]
            url = pg.xpath("./url/text()")[0]

            print "'%s':'%s';" %(db_id,name)
            # 结果list
            result_list = []


            driver.get(url)
            #下拉框获取日期
            script_date = driver.find_element_by_xpath("//select[@name='date']")

            waiter = WebDriverWait(driver, 10)
            script_date = script_date.text.strip().split('\n')

            india_date = (datetime.datetime.utcnow() + datetime.timedelta(hours=5)).strftime('%Y-%m-%d')
            #获取下拉款元素
            select = Select(driver.find_element_by_xpath("//select[@class='custom-select']"))


            #点击下拉框，获取多天数据
            for ii in range(1, len(script_date)):
                select.select_by_index(ii)

                #获取时间
                list_time = waiter.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//table[@class='scheduleContent']/tbody/tr/td[1]"))
                )
                #获取节目
                list_content = waiter.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//table[@class='scheduleContent']/tbody/tr/td[2]"))
                )


                #节目日期
                date_time = (datetime.datetime.strptime(india_date, "%Y-%m-%d") + datetime.timedelta(days=ii)).strftime(
                    '%Y-%m-%d')
                list_time, list_content = clear_data(list_time, list_content)
                result_list.append({date_time: dict(zip(list_time, list_content))})

    except Exception,e:
        print str(e)
        print traceback.format_exc()

    finally:
        #关闭浏览器驱动
        driver.close()
        return result_list

if __name__ == '__main__':
    result_list = get_data()
    print result_list