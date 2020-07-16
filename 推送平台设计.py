# -*- coding:utf-8 -*-
# @Time : 2020/5/19 16:02
# @Author :赵钰中
# @File : 推送平台设计.py
# @Software : PyCharm


import time
import re
import math
import sqlite3
import smtplib
from bs4 import BeautifulSoup
import urllib.request,urllib.error
from email.mime.text import MIMEText
from email.header import Header

#建立网络连接请求
def askUrl(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    }
    req = urllib.request.Request(url=url, headers=headers)
    html = ""
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    return html

#获取和解析网页数据
def getData(url):
    pass
    dataList = []
    date = re.findall(r"\d{4}-\d+-\d+",url)
    html = askUrl(url)
    tiaoshu = re.findall('<a onmouse="">总条数：(\d+)</a>',html)

    if len(tiaoshu)==0:
        print("这一天还没有数据发布，请晚一点再来。")
        return dataList
    else:
        tiaoshu = int(tiaoshu[0])
        print("数据获取中，请等待...")
        bianlicishu = math.ceil(tiaoshu/10)
        jilu = 0
        for i in range(1,bianlicishu+1):
            nurl = url+"&pageno=%d"%i
            html = askUrl(nurl)
            soup = BeautifulSoup(html, "html.parser")
            biaoji = 0
            data = []
            linkall = []
            data1 = []
            for item in soup.find_all(name="a", attrs={"class": "a_title2",
                                            "target": "_blank"}):  # 查找符合要求的字符，形成列表style="margin-top:8px;"

                #遍历找出漏洞名称和漏洞的链接地址以及漏洞的编号
                biaoji = biaoji+1
                jilu  = jilu+1
                name = item.get_text().strip()
                print(jilu,name)
                data.append(name)
                item = str(item)
                link = re.findall(findLink, item)
                link = "http://www.cnnvd.org.cn" + link[0]
                linkall.append(link)
            for item in soup.find_all(name="img",attrs={"border":"0"}):
                jibie = item.get('title')
                if jibie:
                    data1.append(jibie)
                else:
                    data1.append("暂未公布")
            for i in range(biaoji):
                datasd = []
                datasd.append(data1[i])
                datasd.append(data[i])
                datasd.append(linkall[i])
                datasd.append(date[0])
                dataList.append(datasd)
    return dataList


#初始化建立数据库
def init_db(dbpath):
    #创建数据表
    sql = """
            create table if not exists smallcnnvd
            (
            危险等级 varchar,
            漏洞信息名称 varchar NOT NULL PRIMARY KEY,
            漏洞信息链接 text,
            信息更新时间 text,
            信息抓取时间 text)
        """
    conn = sqlite3.connect(dbpath) #打开数据库  (如果不存在，则创建一个并返回一个数据对象，否则就链接数据库)
    cursor = conn.cursor() #获取游标
    cursor.execute(sql) #执行SQL操作
    conn.commit()
    conn.close()
    print("连接数据库成功")


#数据规范化存入数据
def saveData2DB(datalist,dbpath):
    if datalist==[]:
        return
    init_db(dbpath)
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    for data in datalist:
        for index in range(len(data)):
            data[index] = '"'+data[index]+'"'
        sql = '''
        replace into smallcnnvd(
        危险等级,漏洞信息名称,漏洞信息链接,信息更新时间,信息抓取时间) 
        values(%s)'''%(",".join(data)+",date('now')")
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()
    print("信息已经存入数据库中")


#从数据库中调取信息
def getFromDB(date):
        print(type(date))
        print(date)
        conn = sqlite3.connect('cnnvdceshi.db')
        c = conn.cursor()
        cursor = c.execute("SELECT *  from smallcnnvd where 信息更新时间='%s' and (危险等级='超危'or 危险等级='高危')"%date)
        tiaoshubiaoji = 0
        chaowei_num=0
        body = """
            <table border = "1">
              <tr>
                <th>漏洞信息名称</th>
                <th>危险等级</th>
                <th>信息发布时间</th>
              </tr>
            """
        for row in cursor:
                if row[0] == "超危":
                 chaowei_num = chaowei_num+1
                 body1="""
                          <tr>
                            <td><a href="%s">%s</a></td>
                            <td  bgcolor="red">%s</td>
                            <td>%s</td>
                          </tr>
                        """%(row[2],row[1],row[0],row[3])
                else:
                 body1 = """
                          <tr>
                            <td><a href="%s">%s</a></td>
                            <td >%s</td>
                            <td>%s</td>
                          </tr>
                        """ % (row[2], row[1], row[0], row[3])
                body =body+body1
                print ("漏洞危险等级：", row[0])
                print("漏洞名称：", row[1])
                print("漏洞详细链接", row[2])
                print("漏洞信息更新日期", row[3], "\n")
                tiaoshubiaoji=tiaoshubiaoji+1
        top = "<h3>%s日的漏洞信息推送,共有%d条高危级别以上数据</h3>"%(date,tiaoshubiaoji)
        body = top+body+"</table>"
        print("信息已经准备就绪")
        print("其中高危级别以上漏洞的数量共有：%d 条"%tiaoshubiaoji)
        print("高危级别漏洞的数量有：%d 条"%(tiaoshubiaoji-chaowei_num))
        print("超危级别漏洞的数量有：%d 条\n\n\n"%chaowei_num)
        conn.close()
        return body



#发送邮件的函数
def sendEmil(content,to_addr):
        # 发信方的信息：发信邮箱，QQ 邮箱授权码
        from_addr = '1397065061@qq.com'
        password = 'uztxvjvmizkdfhdd'
        # 发信服务器
        smtp_server = 'smtp.qq.com'
        # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
        msg = MIMEText(html, 'html', 'utf-8')
        # 邮件头信息
        msg['From'] = Header(from_addr)
        msg['To'] = Header(to_addr)
        msg['Subject'] = Header('今日份的漏洞信息推送')
        # 开启发信服务，这里使用的是加密传输
        server = smtplib.SMTP_SSL(host=smtp_server)
        server.connect(smtp_server, 465)
        # 登录发信邮箱
        server.login(from_addr, password)
        # 发送邮件
        server.sendmail(from_addr, to_addr, msg.as_string())
        # 关闭服务器
        server.quit()
        print("\n信息发送成功！")


findjibei = re.compile(r'title="(.*?)"')
findLink = re.compile(r'href="(.*?)"')

if __name__ == '__main__':
    today = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    todayUrl = "http://www.cnnvd.org.cn/web/vulnerability/querylist.tag?qstartdateXq=" + today
    url = "http://www.cnnvd.org.cn/web/vulnerability/querylist.tag?qstartdateXq=2020-06-02"
    choose = input("按1选择获取数据，按2选择邮件发送：")
    if choose=="1":
        dataList = getData(url)
        dbpath = "cnnvdceshi.db"
        saveData2DB(dataList,dbpath)

        isSend = input("是否要进行邮件的发送？(y/n)\t")
        if isSend == "y" :
            html = getFromDB(date=today)
            to_addr = '1784012538@qq.com'
            sendEmil(content=html,to_addr=to_addr)
        else:
            print("程序停止")
            pass
    elif choose =="2":
        html = getFromDB(date=today)
        to_addr = '1784012538@qq.com'
        sendEmil(content=html, to_addr=to_addr)
