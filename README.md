# Safety Classifier

AI-powered workplace safety incident classifier built on AWS. Submit a description of a workplace incident and the system automatically classifies its severity, category, and recommended action using Claude via Amazon Bedrock.

## How It Works

1. Send a POST request with an incident description to the API endpoint
2. Lambda function forwards the description to Claude (Anthropic) via Amazon Bedrock
3. Claude classifies the incident and returns structured JSON
4. Result is saved to DynamoDB with a unique incident ID
5. Classification is returned to the caller instantly

## Architecture
```
API Gateway (POST /classify)
       │
       ▼
  Lambda Function
       │
       ├── Amazon Bedrock (Claude) ── classifies incident
       │
       └── DynamoDB ── stores incident + classification
```

## Services Used

| Service | Role |
|---|---|
| API Gateway | Public HTTP endpoint |
| Lambda | Core classification logic |
| Amazon Bedrock | Claude AI model inference |
| DynamoDB | Incident storage |
| CDK | Infrastructure as code |

## Example Request
```bash
curl -X POST https://z6cjwo9j78.execute-api.us-east-1.amazonaws.com/prod/classify \
  -H "Content-Type: application/json" \
  -d '{"description": "Worker slipped on wet floor near loading dock"}'
```

## Example Response
```json
{
  "incident_id": "f8b46802-bafa-43b7-b427-85458307b9d0",
  "classification": {
    "severity": "MEDIUM",
    "category": "Slip and Fall",
    "recommended_action": "Secure the area, provide first aid, and investigate the cause of the wet floor",
    "requires_immediate_attention": true
  }
}
```

## Setup
```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Bootstrap CDK (one time)
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1

# Deploy
cdk deploy
```

## Key Design Decisions

**Why Bedrock over direct Anthropic API?**
Bedrock keeps everything within AWS — same IAM permissions, same billing, same network boundary. No external API keys to manage or rotate.

**Why DynamoDB?**
Each incident is a discrete record accessed by ID. DynamoDB's single-digit millisecond latency and pay-per-request billing make it a natural fit for an event-driven classification system.

**Why API Gateway + Lambda over a containerized service?**
This workload is bursty and unpredictable — Lambda scales to zero when idle and handles spikes automatically. No servers to manage, no minimum cost.
