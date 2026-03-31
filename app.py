import aws_cdk as cdk
from safety_classifier_stack import SafetyClassifierStack

app = cdk.App()

SafetyClassifierStack(
	app,
	"SafetyClassifierStack",
	env = cdk.Environment(
		region = "us-east-1"
	),
)

app.synth()
