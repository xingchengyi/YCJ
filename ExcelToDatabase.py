import xlrd
import sqlite3 as sql

def tran(file):
    db = sql.connect("name.db")
    db.text_factory =  str
    cursor = db.cursor()
    comm = ('''
    CREATE TABLE IF NOT EXISTS NAME
     (
     name NOT NULL,
     schid NOT NULL
     );
    ''')
    cursor.execute(comm)

    data = xlrd.open_workbook(file)
    table = data.sheets()[0]
    value = table.col_values(5)
    valueLen = len(value)
    for i in range(1,valueLen):
        para = (value[i],'80110')
        comm = ("INSERT INTO NAME (name,schid) VALUES (?,?)")
        cursor.execute(comm,para)
    cursor.close()
    db.commit()
    db.close()

file = 'sy2z.xls'
tran(file)