import pandas as pd
from langchain_aws import ChatBedrockConverse
from dotenv import load_dotenv
import boto3
from logic.models import ClassifiedOutput
import re
import json
from logic.prompt import TRANSACTION_EXTRACTION_PROMPT
from typing_extensions import TypedDict, List, Dict

load_dotenv()


region_name = 'us-east-1'
bedrock_client = boto3.client("bedrock-runtime",region_name = 'us-east-1')

slm = ChatBedrockConverse(
    model= "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    client=bedrock_client,
    temperature=0,
)

class AgentState(TypedDict):
    transactions: List[Dict]
    personal_payments: List[Dict]
    top_recipients: List[Dict]
    current_recipient_index: int
    merchant_mappings: Dict[str, str]
    awaiting_user_input: bool
    user_response: str | None

# Node 1: Analyze transactions and find top personal payment recipients
def analyze_personal_payments(state: AgentState) -> AgentState:
    """Extract and analyze personal payments to find top recipients"""
    transactions = state["transactions"]
    
    # Filter personal payments
    personal_payments = [
        t for t in transactions
        if t.get("category") == "Personal Payments"
    ]
    
    # Count frequency of each recipient
    recipient_stats = {}
    for txn in personal_payments:
        recipient = txn.get("recipient_name", "Unknown")
        amount = txn.get("amount", 0)
        
        if recipient not in recipient_stats:
            recipient_stats[recipient] = {
                "name": recipient,
                "count": 0,
                "total_amount": 0,
                "transactions": []
            }
        
        recipient_stats[recipient]["count"] += 1
        recipient_stats[recipient]["total_amount"] += amount
        recipient_stats[recipient]["transactions"].append(txn)
    
    # Sort by transaction count (or you can sort by amount)
    top_recipients = sorted(
        recipient_stats.values(),
        key=lambda x: x["count"],
        reverse=True
    )[:10]  # Get top 10 recipients
    
    return {
        **state,
        "personal_payments": personal_payments,
        "top_recipients": top_recipients,
        "current_recipient_index": 0,
        "merchant_mappings": state.get("merchant_mappings", {}),
        "awaiting_user_input": True
    }
 