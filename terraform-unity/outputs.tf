output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.unity_cs_monitoring_lambda.arn
}
