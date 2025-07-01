from dotenv import load_dotenv
from decouple import config
import os
# 방법 1
load_dotenv('.env')
client_id = os.getenv("Client_ID")
print('방법1 :', client_id)
# 방법2
client_id = config('Client_ID')
print('방법2 :', client_id)