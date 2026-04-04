from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct

class SafetyClassifierStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        incidents_table = dynamodb.Table(
            self,
            "IncidentsTable",
            table_name="safety-incidents",
            partition_key=dynamodb.Attribute(
                name="incident_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # swap to RETAIN before going to prod
        )

        classifier_fn = _lambda.Function(
            self,
            "ClassifierFunction",
            function_name="safety-classifier",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/classifier"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "INCIDENTS_TABLE": incidents_table.table_name,
                "MODEL_ID": "us.anthropic.claude-3-haiku-20240307-v1:0",
            },
        )

        incidents_table.grant_read_write_data(classifier_fn)

        classifier_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )

        api = apigw.RestApi(
            self,
            "SafetyClassifierApi",
            rest_api_name="safety-classifier-api",
            description="Workplace safety incident classifier",
        )

        classifier_integration = apigw.LambdaIntegration(classifier_fn)
        incidents_resource = api.root.add_resource("classify")
        incidents_resource.add_method("POST", classifier_integration)

        CfnOutput(self, "ApiUrl",
            value=f"{api.url}classify",
            description="POST your incident JSON to this URL",
        )

        CfnOutput(self, "TableName",
            value=incidents_table.table_name,
            description="DynamoDB table storing incidents",
        )
