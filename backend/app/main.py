# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.database.session import cursor, conn


app = FastAPI()
app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def execute_sql_script(file_path, conn):
    with open(file_path, 'r') as sql_file:
        sql_script = sql_file.read()

    with conn.cursor() as cursor:
        cursor.execute(sql_script)
        conn.commit()

sql_file_path = 'app/database/init.sql'

execute_sql_script(sql_file_path, conn)
