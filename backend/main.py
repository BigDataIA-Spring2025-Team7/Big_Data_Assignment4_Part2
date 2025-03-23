from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
from dotenv import load_dotenv
import requests

# Optional mistral processor (still processed in FastAPI)
from pdf_processing.mistral import mistral_pdf_to_md

load_dotenv()

# AWS
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")

# Airflow API
AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://airflow-webserver:8080/api/v1")
AIRFLOW_DAG_ID = "dag_pdf_parser_docling"
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "airflow")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "airflow")

app = FastAPI()

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

@app.get("/get_available_years")
def get_available_years():
    response = s3_client.list_objects_v2(Bucket=AWS_BUCKET, Prefix="Raw_PDFs/", Delimiter="/")
    years = [prefix["Prefix"].split("/")[-2] for prefix in response.get("CommonPrefixes", [])]
    return {"years": sorted(years, reverse=True)}

@app.get("/get_available_quarters/{year}")
def get_available_quarters(year: str):
    prefix = f"Raw_PDFs/{year}/"
    response = s3_client.list_objects_v2(Bucket=AWS_BUCKET, Prefix=prefix)
    quarters = [obj["Key"].split("/")[-1].replace(".pdf", "") for obj in response.get("Contents", []) if obj["Key"].endswith(".pdf")]
    return {"quarters": sorted(quarters)}

@app.get("/get_pdf_url/{year}/{quarter}")
def get_pdf_url(year: str, quarter: str):
    s3_key = f"Raw_PDFs/{year}/{quarter}.pdf"
    url = s3_client.generate_presigned_url("get_object", Params={"Bucket": AWS_BUCKET, "Key": s3_key}, ExpiresIn=3600)
    return {"pdf_url": url}

@app.post("/trigger_docling_dag/{year}/{quarter}")
def trigger_docling_dag(year: str, quarter: str):
    try:
        response = requests.post(
            f"{AIRFLOW_URL}/dags/{AIRFLOW_DAG_ID}/dagRuns",
            auth=(AIRFLOW_USERNAME, AIRFLOW_PASSWORD),
            json={"conf": {"year": year, "quarter": quarter}}
        )
        response.raise_for_status()
        return {"message": "✅ Airflow DAG triggered", "run_id": response.json().get("dag_run_id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger DAG: {str(e)}")

@app.post("/process_pdf_mistral/{year}/{quarter}")
def process_pdf_with_mistral(year: str, quarter: str):
    s3_key = f"Raw_PDFs/{year}/{quarter}.pdf"
    try:
        response = s3_client.get_object(Bucket=AWS_BUCKET, Key=s3_key)
        pdf_bytes = response["Body"].read()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"PDF not found in S3: {e}")

    result = mistral_pdf_to_md(pdf_bytes, year, quarter)
    return result
