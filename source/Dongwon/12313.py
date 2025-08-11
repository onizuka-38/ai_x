from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 읽기

print("API KEY:", os.getenv("OPENAI_API_KEY"))
