# -*- codeing = utf-8 -*-
# @Time : 2020/4/12 19:50
# @Author :赵钰中
# @File : py爬虫基础.py
# @Software : PyCharm


"""
需求分析：爬取豆瓣电影Top250的基本信息，
包括电影名称，豆瓣评分，评价数，电影概况，电影链接等
"""


from bs4 import BeautifulSoup  #网页解析，获取数据
import re   #正则表达式，进行文字匹配
import sqlite3 #
import urllib.request,urllib.error  #指定URl，获取网页数据
import xlwt





findLink = re.compile(r'<a href="(.*?)">')  #全局变量
findImage = re.compile(r'<img.*src="(.*?)"',re.S) #re.S 忽略点里面的换行符,直接比对（包含在其中）
findTitle = re.compile(r'<span class="title">(.*?)</span>')
#影片评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*?)</span>')
findJudge = re.compile(r'<span>(\d*)人评价</span>')
findInq = re.compile(r'<span class="inq">(.*)</span>')
#影片的相关内容
findBD = re.compile(r'<p class="">(.*?)</p>',re.S)



def main():
    #爬取网页，解析数据，保存数据
    baseurl = "https://movie.douban.com/top250?start="
    datalist = getData(baseurl)
    savepath = r"C:\Users\ZYZ\Desktop\桌面垃圾\doubantop250_1.xls"
    saveData(datalist,savepath)
    dbpath = "movie.db"
    saveData2DB(datalist,dbpath)


#保存数据
def saveData(dataList,savepath):
    book = xlwt.Workbook(encoding='utf-8',style_compression=0) #以什么编码创建一个Excel对象
    sheet = book.add_sheet("豆瓣电影top250",cell_overwrite_ok=True) #创建一个sheet表格
    col = ("电影详情链接","图片链接","影片中文名","影片外国名","评分","评价人数","概况","电影详情")
    for i in range(0,8):
        sheet.write(0,i,col[i])#列名
    for i in range(0,250):   #往单元格中填写内容
        data = dataList[i]
        for j in range(0,8):
            sheet.write(i+1,j,data[j]) #数据
    book.save(savepath) #保存表格
#得到一个指定URl的网页内容


def saveData2DB(datalist,dbpath):
    pass
    init_db(dbpath)
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    # cur.execute(sql)

    for data in datalist:
        for index in range(len(data)):
            if index == 4 or index ==5:  #第五个数据和第六个数据不需要做改变，可以这么做，但此处不需要这么做也可以
                continue
            data[index] = '"'+data[index]+'"' #网址和什么的不是字符串类型，而放入数据库要编程字符串型。转换成字符串
        sql = '''
            insert into movie250 (
            info_link,pic_link,cname,
            ename,score,rated,instroduction,info)
            values(%s)
            '''%",".join(data) #用join连接一个东西把data列表用join方法连接，中间用逗号隔开，
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()


def init_db(dbpath):
    #创建数据表
    sql = """
        create table movie250
        (id integer primary  key autoincrement,
        info_link text,
        pic_link text,
        cname varchar,
        ename varchar,
        score numeric ,
        rated numeric ,
        instroduction text ,
        info text)
    """
    conn = sqlite3.connect(dbpath) #打开数据库
    cursor = conn.cursor() #获取游标
    cursor.execute(sql) #执行SQL操作
    conn.commit()
    conn.close()
    print("创建数据库成功")


def askUrl(url):
    header = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36"
    } #模拟浏览器头部，向服务器发送消息
    #用户代理，告诉服务器我们是什么类型的浏览器，以及我们可以接受什么水平的显示页面
    req = urllib.request.Request(url,headers=header)
    html = ""
    try:
        response = urllib.request.urlopen(req)

        html = response.read().decode("utf-8")
        # print(html)
        # f = open("cvdn.html","w+",encoding="utf-8") #设置写入编码
        # f.write(html)
        # f.close()
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    return html


#爬取网页
def getData(baseurl):
    dataList = []
    for i in range(0,10):  #调用获取页面信息的函数10次，一页25条
        url = baseurl + str(i*25)
        html = askUrl(url)  #保存获取到的网页源码
        #逐一解析数据

        # soup = BeautifulSoup(html,"html.parser")
        soup = BeautifulSoup(html,"html.parser")
        for item in soup.find_all("div",class_="item"): #查找符合要求的字符，形成列表
            print(item)
            break
            data = []  #保存一部电影的所有信息
            item = str(item)
            #获取到影片详情链接
            link = re.findall(findLink,item)[0]
            data.append(link)

            img = re.findall(findImage,item)[0]
            data.append(img)

            title = re.findall(findTitle,item)
            if(len(title)==2):
                ctitle = title[0] #添加中文名
                data.append(ctitle)
                otitle = title[1].replace("/","") #去掉无关的符号
                data.append(otitle)  #添加外国名
            else:
                data.append(title[0])
                data.append(" ")#外国名留空
            rating = re.findall(findRating,item)[0]
            data.append(rating)  #评分
            judge = re.findall(findJudge,item)[0]
            data.append(judge)  #评价人数

            # print(re.findall(findInq,item))
            inq = re.findall(findInq,item)
            if len(inq) != 0:
                inq = inq[0].replace("。","")
                data.append(inq)  #概述
            else:
                data.append(" ") #留空

            bd = re.findall(findBD,item)[0]
            bd = re.sub('<br(\s+)?/>(\s+)?',"",bd) #去掉<br/>
            bd = re.sub('/'," ",bd)
            data.append(bd.strip()) #去掉前后的空格

            dataList.append(data) #把处理好的一部电影信息放入datalist
        break
    return dataList

if __name__ == '__main__':
    # main()
    getData("https://movie.douban.com/top250?start=")
    print("爬取数据完毕！")

