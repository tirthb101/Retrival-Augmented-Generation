from RAG import Rag
from fastapi import FastAPI, Request, Form, File, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
from utils import get_resource_path
from typing import Dict, List, Any, Callable
from jwt import encode, decode, PyJWTError
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from starlette.responses import Response
from pydantic import BaseModel
from EngToSql import generateSql, getQueryResult
from functools import wraps
from dotenv import load_dotenv
import re

load_dotenv()


if not os.path.exists("db"):
    os.makedirs("db")

secure_attribute = os.getenv("SECURE_ATTRIBUTE")
collection_name = os.getenv("COLLECTION")

rag = Rag(collection_name=collection_name)

app = FastAPI(debug=os.getenv("DEBUG"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
app.mount(
    "/static", StaticFiles(directory=get_resource_path("static")), name="static")

upload_folder = "uploads"
UPLOAD_FOLDER = get_resource_path("uploads")

if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

db = SQL("sqlite:///data.db")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM") if os.getenv("ALGORITHM") else "HS256"


class GeneralAIRequest(BaseModel):
    context: List[Dict[str, Any]] = []

class DBRequest(BaseModel):
    query : str


def token_required(func: Callable):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        token = request.cookies.get('token')
        username = request.cookies.get('username')

        if not token:
            return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

        try:
            data = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if not data['username'] == username:
                return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
        except PyJWTError:
            return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

        return await func(request, *args, **kwargs)

    return wrapper


@app.get("/login")
async def get_login_form():
    return FileResponse(os.path.join(get_resource_path("static"), "login.html"))


@app.get("/register")
async def get_register_form():
    return FileResponse(os.path.join(get_resource_path("static"), "register.html"))

@app.get("/database")
@token_required
async def getDB(request: Request):
    return FileResponse(os.path.join(get_resource_path("static"), "database.html"))


@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
):
    if not username:
        return Response("must provide username", status_code=400)
    elif not password:
        return Response("must provide password", status_code=400)

    try:
        data = db.execute('SELECT * FROM users WHERE username = ?', username)

        if not len(data) > 0 or not check_password_hash(data[0]['password'], password):
            return JSONResponse({
                'data': '',
                'status': 'failed to AUTHENTICATE',
                'code': 401
            })

        token_data = {
            'username': username,
            "role": data[0]["role"],
            "password": password,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=28800)
        }

        token = encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        response = JSONResponse({"message": "success", "username": username})
        response.set_cookie(key='token', value=token, httponly=True,
                            secure=secure_attribute, samesite='Strict', max_age=28800)
        response.set_cookie(key='username', value=username, httponly=True,
                            secure=secure_attribute, samesite='Strict', max_age=28800)
        return response
    except Exception as e:
        return JSONResponse({
            'data': "failed",
            'status': 'an error occured',
            'code': 401
        })


@app.post('/register')
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    if not username:
        return Response("must provide username", status_code=400)
    if not password:
        return Response("must provide password", status_code=400)
    if not role:
        return Response("must provide role", status_code=400)

    data = db.execute('SELECT * FROM users WHERE username = ?', username)

    if not len(data) == 0:
        return JSONResponse({
            'data': 'failed',
            'status': 'account with this username already exist',
            'code': 401
        })

    try:
        db.execute(f"insert into users(username, role, password) values(?, ?, ?)",
                   username, role, generate_password_hash(password))

        token_data = {
            'username': username,
            "role": role,
            'password': password,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=28800)
        }

        token = encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        response = JSONResponse({"message": "success"})
        response.set_cookie(key='token', value=token, httponly=True,
                            secure=secure_attribute, samesite='Strict', max_age=28800)
        response.set_cookie(key='username', value=username, httponly=True,
                            secure=secure_attribute, samesite='Strict', max_age=28800)
        return response

    except Exception as e:
        return JSONResponse({
            'data': '',
            'status': 'an error occured',
            'code': 401
        })


@app.get("/")
@token_required
async def get_query_form(request: Request):
    file_path = os.path.join(get_resource_path("static"), "assistant.html")
    response = FileResponse(file_path)

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.get("/upload")
@token_required
async def get_upload_form(request: Request):
    return FileResponse(os.path.join(get_resource_path("static"), "upload.html"))


@app.get("/assistant")
@token_required
async def get_upload_form(request: Request):
    return FileResponse(os.path.join(get_resource_path("static"), "popup-chat-window.html"))


@app.get("/generalAI")
@token_required
async def get_general_ai(request: Request):
    return FileResponse(os.path.join(get_resource_path("static"), "generalAI.html"))


@app.post("/database")
@token_required
async def postDB(request: Request, request_data: DBRequest):
    before = datetime.datetime.utcnow()
    count = 0
    for i in range(5):
        try:
            count += 1
            sql = generateSql(request_data.query)
            print(sql)
            # sql = re.search(r"(SELECT.*?);(?!\w)", sql, re.IGNORECASE | re.DOTALL).group(0)
            sql = re.search(r"SELECT.*", sql, re.IGNORECASE | re.DOTALL).group(0)
            if not sql:
                raise Exception()
            result = getQueryResult(sql)
            after = datetime.datetime.utcnow()
            if not result:
                continue
            
            return JSONResponse({"sqlQuery": sql, "results": result[1], "headers" : result[0], "shots": count})
        except Exception as e:
            pass
    return JSONResponse({"message": str(e)}, status_code=500)




@app.post("/upload")
@token_required
async def upload_form(
    request: Request,
    files: List[UploadFile] = File(...),
    department: str = Form(...),
):
    if not files:
        return JSONResponse({"message": "No Files Received"}, status_code=400)

    if not department:
        return JSONResponse({"message": "Must provide department"}, status_code=400)

    failed_count = 0
    successfully_uploaded = []
    failed_uploading = []
    total_files = len(files)

    for file in files:
        file_path = os.path.join(
            UPLOAD_FOLDER, str(uuid.uuid4()) + "_" + file.filename)
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            print(file_path)
            print(department)
            rag.add_file(file_path, department)
            successfully_uploaded.append(file.filename)
        except Exception as e:
            print(e.__str__())
            failed_uploading.append(file.filename)
            failed_count += 1
        finally:
            if os.path.isfile(file_path):
                os.remove(file_path)

    successfully_uploaded = list(
        successfully_uploaded)
    failed_uploading = list(failed_uploading)

    return JSONResponse({
        "total_files": total_files,
        "success": successfully_uploaded,
        "failed": failed_uploading
    }, status_code=200 if failed_count == 0 else 500)


@app.post("/ask")
@token_required
async def ask_query(
    request: Request,
    query: str = Form(...),
    department: str = Form(...),
):
    before = datetime.datetime.utcnow()
    if not query:
        return JSONResponse({'message': "Please provide a Query"})
    if not department:
        return JSONResponse({'message': "Please provide a Department"})

    try:
        db.execute(f"insert into messages(username, message) values(?, ?)",
                   request.cookies.get('username'), query)
        message = await rag.query(query, department)
        after = datetime.datetime.utcnow()
        return JSONResponse({"message": message["message"]["content"], "time": str(after - before)})
    except Exception as e:
        return JSONResponse({"message": "Couldn't process request", "error": str(e)}, status_code=500)


# @app.post("/ask")
# @token_required
# async def ask_query(
#     request: Request,
#     query: str = Form(...),
#     department: str = Form(...),
# ):
#     if not query:
#         return JSONResponse({'message': "Please provide a Query"})
#     if not department:
#         return JSONResponse({'message': "Please provide a Department"})

#     def event_generator():
#         try:
#             # Get the iterator from rag.query
#             response_iterator: Iterator = rag.query(query, department)

#             for chunk in response_iterator:
#                 if hasattr(chunk, 'message') and chunk.message.content:
#                     # Send each chunk as an SSE event
#                     yield {
#                         "event": "message",
#                         "data": chunk.message.content
#                     }

#             # Send a done event
#             yield {
#                 "event": "done",
#                 "data": ""
#             }

#         except Exception as e:
#             yield {
#                 "event": "error",
#                 "data": str(e)
#             }

#     return EventSourceResponse(event_generator())


# @app.post("/askGeneral")
# @token_required
# async def ask_general(
#     request: Request,
#     request_data: GeneralAIRequest,
# ):
#     if not request_data:
#         return JSONResponse({'message': "Please provide a Query"})
#     # if not department:
#     #     return JSONResponse({'message': "Please provide a Department"})
#     print(request_data)

#     def event_generator():
#         try:
#             # Get the iterator from rag.query
#             response_iterator: Iterator = rag.chat_with_model(
#                 request_data.context)

#             for chunk in response_iterator:
#                 if hasattr(chunk, 'message') and chunk.message.content:
#                     yield {
#                         "event": "message",
#                         "data": chunk.message.content
#                     }

#             # Send a done event
#             yield {
#                 "event": "done",
#                 "data": ""
#             }

#         except Exception as e:
#             yield {
#                 "event": "error",
#                 "data": str(e)
#             }

#     return EventSourceResponse(event_generator())

@app.post("/askGeneral")
@token_required
async def ask_general(
    request: Request,
    request_data: GeneralAIRequest,
):
    before = datetime.datetime.utcnow()
    try:
        if request_data.context[-1]["role"] != "system":
            db.execute(f"insert into messages(username, message) values(?, ?)",
                       request.cookies.get('username'), request_data.context[-1]["content"].__str__())
        message = rag.chat_with_model(request_data.context)
        after = datetime.datetime.utcnow()
        return JSONResponse({"message": message["message"]["content"], "time": str(after - before)})
    except Exception as e:
        return JSONResponse({"message": str(e)}, status_code=500)


@app.get('/logout')
async def logout():
    response = RedirectResponse(
        "/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('username')
    response.delete_cookie('token')
    return response


@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    return RedirectResponse(url="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fast-app:app", host="127.0.0.4", port=4000, reload=os.getenv("RELOAD"))
