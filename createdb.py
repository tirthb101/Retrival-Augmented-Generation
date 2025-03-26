from cs50 import SQL


db = SQL("sqlite:///data.db")


db.execute(
    "create table users(username VARCHAR(20) primary key, role VARCHAR(20) not null, password VARCHAR(40) not null);")

db.execute("create table messages(id integer primary key autoincrement, username VARCHAR(20) not null, message TEXT not null, created_at DEFAULT CURRENT_TIMESTAMP);")
