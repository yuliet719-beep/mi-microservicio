terraform {
  required_version = ">= 1.9.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}
variable "project_id" { type = string }
variable "region" { default = "us-central1" }
variable "db_password" {
  type      = string
  sensitive = true
}
provider "google" {
  project = var.project_id
  region  = var.region
}
resource "google_project_service" "api" {
  for_each           = toset(["compute.googleapis.com", "sqladmin.googleapis.com", "servicenetworking.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com", "securitycenter.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}
resource "google_compute_network" "lab" {
  name                    = "actividad3-sandbox"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.api]
}
resource "google_compute_subnetwork" "lab" {
  name          = "actividad3-sandbox"
  network       = google_compute_network.lab.id
  ip_cidr_range = "10.84.0.0/24"
  region        = var.region
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 1.0
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
resource "google_compute_global_address" "private" {
  name          = "actividad3-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.lab.id
}
resource "google_service_networking_connection" "private" {
  network                 = google_compute_network.lab.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private.name]
}
resource "google_sql_database_instance" "lab" {
  name                = "actividad3-observability"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = true
  depends_on          = [google_service_networking_connection.private]
  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.lab.id
      ssl_mode        = "ENCRYPTED_ONLY"
    }
    backup_configuration { enabled = true }
    insights_config { query_insights_enabled = true }
  }
}
resource "google_sql_database" "lab" {
  name     = "observability"
  instance = google_sql_database_instance.lab.name
}
resource "google_sql_user" "lab" {
  name     = "lab"
  instance = google_sql_database_instance.lab.name
  password = var.db_password
}
resource "google_service_account" "vm" {
  account_id = "actividad3-sandbox"
}
resource "google_project_iam_member" "telemetry" {
  for_each = toset(["roles/logging.logWriter", "roles/monitoring.metricWriter"])
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.vm.email}"
}
resource "google_compute_firewall" "iap" {
  name          = "actividad3-iap-ssh"
  network       = google_compute_network.lab.id
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["actividad3"]
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}
resource "google_compute_instance" "lab" {
  name         = "actividad3-sandbox"
  machine_type = "e2-standard-2"
  zone         = "${var.region}-a"
  tags         = ["actividad3"]
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 30
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.lab.id
    access_config {}
  }
  metadata = { enable-oslogin = "TRUE" }
  service_account {
    email  = google_service_account.vm.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}
output "vm_name" { value = google_compute_instance.lab.name }
output "cloudsql_host" { value = google_sql_database_instance.lab.private_ip_address }
