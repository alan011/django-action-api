import MySQLdb


class MysqlClient(object):
    def __init__(self, host, port, db, user, passwd, charset='utf8'):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.passwd = passwd
        self.charset = charset

    def connect(self, cursorclass=None):
        err = None
        try:
            self.client = MySQLdb.connect(host=self.host, port=self.port, db=self.db, user=self.user, passwd=self.passwd, charset=self.charset)
            self.cursor = self.client.cursor(cursorclass=cursorclass)
        except Exception as e:
            err = str(e)
        return err

    def query(self, sql):
        c = self.cursor
        try:
            c.execute(sql)
        except Exception as e:
            return None, str(e)
        return c.fetchall(), None

    def disconnect(self):
        self.cursor.close()
        self.client.close()

    def commit(self):
        try:
            self.client.commit()
        except Exception as e:
            self.client.rollback()
            return 'SQL client commit failed: ' + str(e)

    def rollback(self):
        self.client.rollback()


class AlpacaMysqlClient(MysqlClient):
    def __init__(self, host, port, db, user, passwd, charset='utf8'):
        MysqlClient.__init__(self, host, port, db, user, passwd, charset='utf8')
    
    def ssdQuery(self, sql=''):
        c = self.client.cursor(cursorclass=MySQLdb.cursors.SSDictCursor)
        c.execute(sql)
        for row in c:
            yield row

    def dictQuery(self, sql=''):
        c = self.client.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        data = None
        while True:
            sql = (yield data)
            c.execute(sql)
            data = c.fetchall()
