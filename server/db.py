import sqlite3 as sql
from sqlite3 import Cursor
from pathlib import Path


def create_connection():
    mod_path = Path(__file__).parent.parent
    con = sql.connect(str(mod_path) + "/hids.db")
    return con


class SQLExecutor:
    def __init__(self, con):
        self.con = con

    def execute(self, queryString, args=()) -> Cursor:
        cur = self.con.cursor()
        executed = cur.execute(queryString, args)
        return executed

    def script(self, script) -> Cursor:
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
        executor.execute('''PRAGMA foreign_keys = ON;''')
    return executor

