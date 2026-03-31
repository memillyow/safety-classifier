import json
import os
import uuid
import boto3
from datetime import datetime, timezone

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# Environment variables
INCIDENTS_TABLE = os.environ["INCIDENTS_TABLE"]
MODEL_ID = os.environ["MODEL_ID"]

table = dynamodb.Table(INCIDENTS_TABLE)

def classify_incident(description: str) -> dict:
    prompt = f"""You are a workplace safety expert. Analyze this incident and respond with JSON only. No other text.

Incident: {description}

Respond with this exact JSON format:
{{
    "severity": "LOW or MEDIUM or HIGH or CRITICAL",
    "category": "category of incident",
    "recommended_action": "what should be done immediately",
    "requires_immediate_attention": true or false
}}"""

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }),
    )

    result = json.loads(response["body"].read())
    text = result["content"][0]["text"].strip()
    
    # Strip markdown code blocks if Claude wraps response in them
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    return json.loads(text)

def save_incident(description: str, classification: dict) -> str:
    incident_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "incident_id": incident_id,
            "timestamp": timestamp,
            "description": description,
            "severity": classification["severity"],
            "category": classification["category"],
            "recommended_action": classification["recommended_action"],
            "requires_immediate_attention": classification["requires_immediate_attention"],
        }
    )

    return incident_id

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        description = body["description"]

        classification = classify_incident(description)
        incident_id = save_incident(description, classification)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "incident_id": incident_id,
                "classification": classification,
            }),
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
