resource "null_resource" "download_lambda_zip" {
  provisioner "local-exec" {
    command = "wget -O ${path.module}/unity-cs-monitoring-lambda.zip https://github.com/unity-sds/unity-cs-monitoring-lambda/releases/download/v1.0.7/unity-cs-monitoring-lambda.zip"
  }
}

resource "aws_lambda_function" "unity_cs_monitoring_lambda" {
  function_name    = "unity_cs_monitoring_lambda"
  role             = "arn:aws:iam::429178552491:role/iam_for_lambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 300  # Timeout set to 5 minutes (300 seconds)

  filename         = "${path.module}/unity-cs-monitoring-lambda.zip"

  environment {
    variables = {
      # Add any environment 
    }
  }

  depends_on = [null_resource.download_lambda_zip]
}
