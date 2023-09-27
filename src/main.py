import os

from dotenv import load_dotenv
import asyncio

from db import Database
from postupi import PostupiOnline
from models import *


ENV_PATH = ".env"
enviroment = load_dotenv(ENV_PATH)
if not enviroment:
    exit(f"Not Founded enviroment file: {ENV_PATH}")


async def main():
    database = Database(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        dbname=os.getenv("MYSQL_DBNAME"),
    )

    await database.Connect()

    parser = PostupiOnline(database)
    await parser.Run()

    database.Close()


if __name__ == "__main__":
    asyncio.run(main())