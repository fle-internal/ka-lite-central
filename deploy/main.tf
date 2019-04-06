terraform {
  backend "gcs" {
    bucket = "ka-lite-central-tfstate"
  }
}

resource "google_sql_database_instance" "master" {
    project = "ka-lite-236721"
    name = "ka-lite-central-${terraform.workspace}"
    database_version = "MYSQL_5_7"
    region = "us-central1"

    settings {
      # Second-generation instance tiers are based on the machine
      # type. See argument reference below.
      tier = "db-n1-standard-4"
      backup_configuration {
        binary_log_enabled = true
        enabled = true
      }
    }
}

