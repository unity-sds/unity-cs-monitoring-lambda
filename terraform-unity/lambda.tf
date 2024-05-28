resource "aws_ssm_parameter" "test_parameter" {
  name  = var.parameter_name
  type  = "String"
  value = var.parameter_value
}
