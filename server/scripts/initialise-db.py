import db

with open('../initialise.sql', 'r') as sql_file:
    sql_script = sql_file.read()


executor = db.use_executor()
executor.script(sql_script)


executor.done()
