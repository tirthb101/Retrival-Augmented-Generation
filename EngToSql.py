import mysql.connector
import ollama
from dotenv import load_dotenv
import os
load_dotenv()

mydb = mysql.connector.connect(
    host=os.getenv("SQLHOST"),
    user=os.getenv("SQLUSER"),
    password=os.getenv("PASSWORD")
)

mydb._execute_query(f"use {os.getenv("DB")};")

curser = mydb.cursor()
with open("schema.txt", "r") as f:
    schema = f.read()

# mydb._execute_query(
# "create table users(username VARCHAR(20) primary key, role VARCHAR(20) not null, password VARCHAR(40) not null);")
# mydb._execute_query(
# "create table messages(id integer primary key AUTO_INCREMENT, username VARCHAR(20) not null, message TEXT not null, created_at TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP);")


def generateSql(query):
    prompt = f""" 
### Instructions:
Your task is to convert a question into a SQL query for a MySQL database. Follow these rules carefully:

1. **Schema Analysis**:
   - Examine the database schema thoroughly to understand tables, columns, relationships
   - Note primary keys, foreign keys, and column data types

2. **Query Construction**:
   - Always use table aliases for clarity (e.g., `SELECT t1.col1, t2.col2 FROM table1 t1 JOIN table2 t2...`)
   - For ratios, explicitly cast the numerator as FLOAT (e.g., `CAST(COUNT(*) AS FLOAT)/...`)
   - Never use the NULLS keyword (not supported in MySQL/SQL Server)
   
3. **Null Handling**:
   - Use COALESCE() or IFNULL() when you need to replace NULL values
   - Filter out NULLs using explicit conditions: 
     - `WHERE column IS NOT NULL` instead of `WHERE column != NULL`
     - `WHERE column IS NULL` when needed
   - For sorting, handle NULLs explicitly:
     - `ORDER BY column DESC` (NULLs last by default in MySQL)
     - `ORDER BY column IS NOT NULL, column DESC` if you want NULLs first

4. **Output Requirements**:
   - Generate clean, optimized SQL that would work in MySQL 8.0+
   - Include only the SQL query in your response, no additional commentary
   - Format the query for readability with appropriate indentation

### Input:
Question: {query}
Database Schema: {schema}

### Response:
```sql
"""
    return ollama.chat(model="sqlcoder", messages=[{"role": "user", "content": prompt}])['message']["content"].replace("NULLS LAST", "").replace("ilike", "like").replace("`","").replace("'", "")


def getQueryResult(query):
    curser.execute(query)
    return [desc[0] for desc  in curser.description], curser.fetchall()

# db = SQL("sqlite:///data.db")


# db.execute(
#     "create table users(username VARCHAR(20) primary key, role VARCHAR(20) not null, password VARCHAR(40) not null);")

# db.execute("create table messages(id integer primary key autoincrement, username VARCHAR(20) not null, message TEXT not null, created_at DEFAULT CURRENT_TIMESTAMP);")
