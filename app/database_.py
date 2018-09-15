import minidb
import time

#https://github.com/thp/minidb

def store_sqlite(company, uuid, endpoint, status):
    db = minidb.Store('data/Apicall.db', debug=True)

    class Call(minidb.Model):
      company = str
      uuid = str
      time = str
      endpoint = str
      status = str

    db.register(Call)

    p = Call(company=company, uuid=uuid, time=str(time.asctime(time.localtime(time.time()))), endpoint = endpoint, status = status)

    p.save(db)

    # retrive = Call.load(db, (Call.c.company == 'sime'))
    #
    # for i in retrive:
    #     print(i)

    db.commit()
    db.close()
