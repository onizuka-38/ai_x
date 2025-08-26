import os
import pandas as pd
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY"),
)

df = pd.read_csv("data/samples.csv")
TEST_COUNT = 20
success = 0

for i,count in enumerate(range(TEST_COUNT)):
    random_index = random.randrange(1,16542)
    response = client.responses.create(
        model="gpt-4o",
        instructions="""""",
        input=df.iloc[random_index]['user_prompt'],
        temperature=0.4
    )
    answer = str(df.iloc[random_index,1])+','+str(df.iloc[random_index,2])+','+str(df.iloc[random_index,3])+','+str(df.iloc[random_index,4])
    if response.output_text.strip() != answer:
        print(f'{count+1}:',df.iloc[random_index]['user_prompt'])
        print('정답:',answer)
        print('GPT:',response.output_text)
    else:
        success += 1
    
print('정답률:',success/TEST_COUNT)