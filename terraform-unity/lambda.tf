resource "null_resource" "download_lambda_zip" {
  provisioner "local-exec" {
    command = "wget -O ${path.module}/unity-cs-monitoring-lambda.zip https://github.com/unity-sds/unity-cs-monitoring-lambda/releases/download/v1.0.24/unity-cs-monitoring-lambda.zip"
  }
}

data "aws_iam_policy" "mcp_operator_policy" {
  name = "mcp-tenantOperator-AMI-APIG"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "unity-cs-monitoring-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  permissions_boundary = data.aws_iam_policy.mcp_operator_policy.arn
}

resource "aws_iam_policy" "lambda_ssm_s3_policy" {
  name        = "unity-cs-monitoring-lambda-policy"
  description = "Policy to allow Lambda to read/write SSM and send objects to S3"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:PutParameter",
          "ssm:DescribeParameters"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_ssm_s3_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_ssm_s3_policy.arn
}

resource "aws_lambda_function" "unity_cs_monitoring_lambda" {
  function_name    = "unity_cs_monitoring_lambda"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 300  # Timeout set to 5 minutes (300 seconds)

  filename         = "${path.module}/unity-cs-monitoring-lambda.zip"

  environment {
    variables = {
      VENUE   = var.venue
      PROJECT = var.project
    }
  }

  depends_on = [null_resource.download_lambda_zip, aws_iam_role_policy_attachment.attach_ssm_s3_policy]
}

resource "aws_cloudwatch_event_rule" "every_five_minutes" {
  name                = "every_five_minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.every_five_minutes.name
  target_id = "invoke_lambda_function"
  arn       = aws_lambda_function.unity_cs_monitoring_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.unity_cs_monitoring_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_five_minutes.arn
}
