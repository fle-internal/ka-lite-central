terraform {
  backend "gcs" {
    bucket = "ka-lite-central-tfstate"
  }
}

resource "google_sql_database" "ka-lite-central" {
  project  = "ka-lite-236721"
  name     = "ka_lite_central"
  instance = "${google_sql_database_instance.master.name}"
  charset  = "utf8"
}

resource "google_sql_database_instance" "master" {
  project          = "ka-lite-236721"
  name             = "ka-lite-central-${terraform.workspace}"
  database_version = "MYSQL_5_7"
  region           = "us-central1"

  settings {
    # Second-generation instance tiers are based on the machine
    # type. See argument reference below.
    tier = "db-n1-standard-4"

    backup_configuration {
      binary_log_enabled = true
      enabled            = true
    }
  }
}

resource "google_sql_database_instance" "replica" {
  project              = "ka-lite-236721"
  name                 = "ka-lite-central-${terraform.workspace}-replica"
  database_version     = "MYSQL_5_7"
  region               = "us-central1"
  master_instance_name = "ka-lite-central-${terraform.workspace}"

  settings {
    tier = "db-n1-standard-4"
  }

  replica_configuration {
    failover_target = true
  }
}
