variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "instance_name" {
  type = string
}

variable "database_name" {
  type    = string
  default = "n8n"
}

variable "database_user" {
  type    = string
  default = "n8n"
}

variable "database_password" {
  type      = string
  sensitive = true
}