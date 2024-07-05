variable "venue" {
  description = "The venue for the deployment"
  type        = string
}

variable "project" {
  description = "The project name"
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to the resources."
  type        = map(string)
}

variable "installprefix" {
  description = "A prefix used for installation."
  type        = string
}

variable "deployment_name" {
  description = "The name of the deployment."
  type        = string
}
