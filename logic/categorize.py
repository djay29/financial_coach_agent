import pandas as pd
from langchain_aws import ChatBedrockConverse
from dotenv import load_dotenv
import boto3
from models import ClassifiedOutput
import re
import json
from prompt import TRANSACTION_EXTRACTION_PROMPT
from typing_extensions import TypedDict, List, Dict

load_dotenv()

region_name = 'us-east-1'
bedrock_client = boto3.client("bedrock-runtime",region_name = 'us-east-1')

slm = ChatBedrockConverse(
    model= "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    client=bedrock_client,
    temperature=0,
)
def main(file_path: str):
    df =pd.read_excel(file_path)

    df.drop(index = 0,inplace=True)
    # df.drop(columns=["Date","Chq./Ref.No.","Value Dt","Closing Balance"],inplace=True)
    df["Trancection"]=df['Deposit Amt.'].fillna(-df["Withdrawal Amt."])
    df.drop(columns=["Withdrawal Amt.","Deposit Amt."],inplace=True)

    lst = []
    iterations = len(df)//100 +1
    split_pos = 0
    for i in range(iterations):
        item = list(df['Narration'][split_pos:split_pos+100])
        lst.append(item)
        split_pos += 100

    json_schema = ClassifiedOutput.model_json_schema()

    result = []
    for i in range(len(lst)):
        prompt = TRANSACTION_EXTRACTION_PROMPT.format(
            json_schema=json_schema,  # <-- Schema tells LLM exact structure to return
            transaction = lst[i]
        )

        response = slm.invoke(prompt)
        # print(response.content)
        json_pattern = r'```json(.*?)```'
        json_match = re.search(json_pattern, response.content, re.DOTALL)

        if not json_match:
            print("  -> ERROR: Could not extract JSON data from AI response.")

        result_json_str = json_match.group(1)
        result_data = json.loads(result_json_str)
        result.extend(result_data)

    with open("categorized_transactions.json", "w") as f:
        json.dump(result, f, indent=4)