from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import os
import io
import logging

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Setup S3
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# DAG args
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# --- Download Task ---
def download_pdf_from_s3(year, quarter, **kwargs):
    key = f"Raw_PDFs/{year}/{quarter}.pdf"
    local_path = f"/tmp/{quarter}.pdf"

    try:
        # Check file exists
        s3.head_object(Bucket=AWS_BUCKET, Key=key)
        s3.download_file(AWS_BUCKET, key, local_path)
        logging.info(f"✅ Downloaded {key} to {local_path}")
        kwargs['ti'].xcom_push(key='pdf_path', value=local_path)
    except Exception as e:
        logging.error(f"❌ Failed to download {key} from S3: {str(e)}")
        raise

# --- Convert Task ---
def convert_pdf_and_upload(year, quarter, **kwargs):
    pdf_path = kwargs['ti'].xcom_pull(key='pdf_path')
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF file path missing or does not exist.")

    # Minimal Docling options
    pipeline_opts = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=True,
        generate_page_images=False,
        generate_picture_images=False,
        images_scale=1.0
    )

    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)}
    )

    result = converter.convert(pdf_path)
    base_path = f"docling_markdown/{year}/{quarter}"

    # Generate Markdown
    markdown = result.document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
    markdown_key = f"{base_path}/{quarter}.md"

    # Upload
    s3.upload_fileobj(io.BytesIO(markdown.encode("utf-8")), AWS_BUCKET, markdown_key)
    logging.info(f"✅ Uploaded markdown to s3://{AWS_BUCKET}/{markdown_key}")

    return {
        "markdown_key": markdown_key,
        "preview_url": f"https://{AWS_BUCKET}.s3.amazonaws.com/{markdown_key}"
    }

# --- Define DAG ---
with DAG(
    dag_id="dag_pdf_parser_docling",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["docling", "markdown"],
) as dag:

    def extract_conf(**kwargs):
        return kwargs["dag_run"].conf["year"], kwargs["dag_run"].conf["quarter"]

    def extract_and_download(**kwargs):
        year, quarter = extract_conf(**kwargs)
        return download_pdf_from_s3(year, quarter, **kwargs)

    def transform_and_upload(**kwargs):
        year, quarter = extract_conf(**kwargs)
        return convert_pdf_and_upload(year, quarter, **kwargs)

    # Tasks
    download_task = PythonOperator(
        task_id="download_pdf_from_s3",
        python_callable=extract_and_download,
        provide_context=True,
    )

    convert_upload_task = PythonOperator(
        task_id="convert_pdf_and_upload_markdown",
        python_callable=transform_and_upload,
        provide_context=True,
    )

    # DAG Flow
    download_task >> convert_upload_task
