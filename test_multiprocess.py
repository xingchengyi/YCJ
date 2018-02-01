#-*- coding: UTF-8 -*-
import multiprocessing as multp
import os
import main
import sqlite3 as sql

def ListName(database):
    db = sql.connect(database)
    cursor = db.cursor()
    comm = "SELECT * FROM NAME"
    cursor.execute(comm)
    value = cursor.fetchall()
    return value

def Get(pair):
    name,schid = pair
    main.log.info("Run child process "+str(os.getpid()))
    userid, stuid, ptpn1 = main.GetStudentId(schid, name)
    print userid,stuid,ptpn1
    ptpn = str(ptpn1)
    pn = main.GetPn(userid, ptpn)
    main.Output(name, stuid, pn, userid)


if __name__ == '__main__':
    db = 'name.db'
    namlist = ListName(db)
    pool = multp.Pool(50)
    for i in namlist:
        pool.apply_async(Get,args=(i,))
    pool.close()
    pool.join()

