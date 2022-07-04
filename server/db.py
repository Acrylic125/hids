import sqlite3 as sql


def create_connection():
    con = sql.connect("hids.db")
    return con


class SQLExecutor:
    def __init__(self, con):
        self.con = con

    def execute(self, queryString, args=()):
        cur = self.con.cursor()
        executed = cur.execute(queryString, args)
        return executed

    def script(self, script):
        cur = self.con.cursor()
        executed = cur.executescript(script)
        return executed

    def commit(self):
        self.con.commit()

    def done(self):
        self.commit()
        self.con.close()


def use_executor(fk_constraints=True):
    con = create_connection()
    executor = SQLExecutor(con)
    if fk_constraints:
        executor.execute("PRAGMA foreign_keys = ON;")
    return executor

