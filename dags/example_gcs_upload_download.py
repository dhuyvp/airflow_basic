
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyDatasetOperator, BigQueryCheckOperator
from airflow.providers.google.cloud.operators.gcs import GCSCreateBucketOperator, GCSDeleteBucketOperator
from airflow.providers.google.cloud.transfers.gcs_to_local import GCSToLocalFilesystemOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

from airflow.utils.trigger_rule import TriggerRule

# ENV_ID = os.environ.get("SYSTEM_TESTS_ENV_ID")
PROJECT_ID = "lucky-altar-388615"

# DAG_ID = "gcs_upload_download"
DAG_ID = "local_gcd_etl_basic"

BUCKET_NAME = "dhuyvp_bucket"
FILE_NAME = "mock_users.csv"
PATH_TO_SAVED_FILE =  "/tmp/mock_users.csv"
# UPLOAD_FILE_PATH = str('/opt/airflow/resources/') + FILE_NAME
UPLOAD_FILE_PATH = "/tmp/mock_users.csv"
# UPLOAD_FILE_PATH = PATH_TO_SAVED_FILE +'/'+ FILE_NAME
print(UPLOAD_FILE_PATH)

DATASET_NAME = "dhuyvp_dataset"
TABLE_NAME = "mock_users_dhuyvp"

with DAG(
    DAG_ID,
    schedule="@once",
    start_date=datetime(2023, 8, 8),
    catchup=False,
    tags=["gcs", "example"],
) as dag:
    # [START howto_operator_gcs_create_bucket]
    create_bucket = GCSCreateBucketOperator(
        task_id="create_bucket",
        bucket_name=BUCKET_NAME,
        gcp_conn_id="admin",
        project_id=PROJECT_ID,
    )
    ######
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset",
        dataset_id=DATASET_NAME,
        project_id=PROJECT_ID,
        gcp_conn_id="admin",
    )


    download_file = BashOperator(
        task_id="download_file_using_BashOperator",
        bash_command = f'curl "https://api.mockaroo.com/api/6872a950?count=1000&key=5f671810" > {PATH_TO_SAVED_FILE}',
    )
    # [START howto_operator_local_filesystem_to_gcs]
    upload_file = LocalFilesystemToGCSOperator(
        task_id="upload_file",
        src=UPLOAD_FILE_PATH,
        dst=FILE_NAME,
        gcp_conn_id="admin",
        bucket=BUCKET_NAME,
    )
    load_csv = GCSToBigQueryOperator(
        gcp_conn_id="admin",
        task_id="gcs_to_bigquery_example",
        bucket="dhuyvp_bucket",
        source_objects=["mock_users.csv"],
        destination_project_dataset_table=f"{DATASET_NAME}.{TABLE_NAME}",
        schema_fields=[
            {"name": "id", "type": "INT64", "mode": "NULLABLE"},
            {"name": "first_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "last_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "email", "type": "STRING", "mode": "NULLABLE"},
            {"name": "gender", "type": "STRING", "mode": "NULLABLE"},
            {"name": "ip_address", "type": "STRING", "mode": "NULLABLE"},

            # id,first_name,last_name,email,gender,ip_address
        ],
        write_disposition="WRITE_TRUNCATE",
    )

    download_file >> [create_bucket, create_dataset] >> upload_file >> load_csv
