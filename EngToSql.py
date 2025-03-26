import mysql.connector
import ollama

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root123",
    password="root@123"
)

mydb._execute_query("use erda;")

curser = mydb.cursor()
# mydb._execute_query(
# "create table users(username VARCHAR(20) primary key, role VARCHAR(20) not null, password VARCHAR(40) not null);")
# mydb._execute_query(
# "create table messages(id integer primary key AUTO_INCREMENT, username VARCHAR(20) not null, message TEXT not null, created_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP);")


def generateSql(query, schema):
    return ollama.chat(model="sqlcoder", messages=[{"role": "user", "content": prompt}])


def getQueryResult(query):
    curser.execute(query)
    return curser.fetchall()

# db = SQL("sqlite:///data.db")


# db.execute(
#     "create table users(username VARCHAR(20) primary key, role VARCHAR(20) not null, password VARCHAR(40) not null);")

# db.execute("create table messages(id integer primary key autoincrement, username VARCHAR(20) not null, message TEXT not null, created_at DEFAULT CURRENT_TIMESTAMP);")
