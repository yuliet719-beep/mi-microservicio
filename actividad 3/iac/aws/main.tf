terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.region }
variable "region" { default = "us-east-1" }
variable "db_password" {
  type      = string
  sensitive = true
}
resource "aws_vpc" "lab" {
  cidr_block           = "10.83.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "actividad3-sandbox" }
}
data "aws_availability_zones" "available" { state = "available" }
resource "aws_subnet" "lab" {
  count             = 2
  vpc_id            = aws_vpc.lab.id
  cidr_block        = "10.83.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
}
resource "aws_internet_gateway" "lab" { vpc_id = aws_vpc.lab.id }
resource "aws_route_table" "internet" {
  vpc_id = aws_vpc.lab.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }
}
resource "aws_route_table_association" "vm" {
  subnet_id      = aws_subnet.lab[0].id
  route_table_id = aws_route_table.internet.id
}
resource "aws_security_group" "vm" {
  name   = "actividad3-vm-no-ingress"
  vpc_id = aws_vpc.lab.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_security_group" "db" {
  name   = "actividad3-rds-private"
  vpc_id = aws_vpc.lab.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.vm.id]
  }
}
resource "aws_db_subnet_group" "lab" { subnet_ids = aws_subnet.lab[*].id }
resource "aws_db_instance" "lab" {
  identifier                = "actividad3-sandbox"
  engine                    = "postgres"
  instance_class            = "db.t3.micro"
  allocated_storage         = 20
  storage_encrypted         = true
  db_name                   = "observability"
  username                  = "lab"
  password                  = var.db_password
  db_subnet_group_name      = aws_db_subnet_group.lab.name
  vpc_security_group_ids    = [aws_security_group.db.id]
  publicly_accessible       = false
  backup_retention_period   = 1
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "actividad3-final"
  tags                      = { "devops-guru-actividad3" = "sandbox" }
}
resource "aws_iam_role" "vm" {
  name = "actividad3-sandbox-vm"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole"
  }] })
}
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.vm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
resource "aws_iam_instance_profile" "vm" { role = aws_iam_role.vm.name }
data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
resource "aws_instance" "lab" {
  ami                         = data.aws_ssm_parameter.ami.value
  instance_type               = "t3.large"
  subnet_id                   = aws_subnet.lab[0].id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.vm.id]
  iam_instance_profile        = aws_iam_instance_profile.vm.name
  metadata_options { http_tokens = "required" }
  root_block_device {
    volume_size = 30
    encrypted   = true
  }
  tags = { Name = "actividad3-sandbox" }
}
resource "aws_cloudwatch_log_group" "flow" {
  name              = "/actividad3/vpc-flow"
  retention_in_days = 7
}
resource "aws_iam_role" "flow" {
  name = "actividad3-flow-logs"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Principal = { Service = "vpc-flow-logs.amazonaws.com" }, Action = "sts:AssumeRole"
  }] })
}
resource "aws_iam_role_policy" "flow" {
  role = aws_iam_role.flow.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect   = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogGroups", "logs:DescribeLogStreams"],
    Resource = [aws_cloudwatch_log_group.flow.arn, "${aws_cloudwatch_log_group.flow.arn}:*"]
  }] })
}
resource "aws_flow_log" "lab" {
  iam_role_arn    = aws_iam_role.flow.arn
  log_destination = aws_cloudwatch_log_group.flow.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.lab.id
}
resource "aws_securityhub_account" "lab" {
  enable_default_standards = false
}
output "instance_id" { value = aws_instance.lab.id }
output "rds_host" { value = aws_db_instance.lab.address }
