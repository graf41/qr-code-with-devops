from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import qrcode
import boto3
import os
from io import BytesIO
import uuid

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# CORS
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STORAGE CONFIG
STORAGE_MODE = os.getenv("STORAGE_MODE", "local") 
LOCAL_STORAGE_PATH = "./data"

os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

# AWS S3 CONFIG
bucket_name = os.getenv("AWS_BUCKET_NAME")

if STORAGE_MODE == "s3":
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    )

@app.post("/generate-qr/")
async def generate_qr(url: str):
    # Generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # LOCAL STORAGE MODE
    if STORAGE_MODE == "local":
        filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(LOCAL_STORAGE_PATH, filename)

        img.save(file_path)

        return {
            "mode": "local",
            "file": filename
        }

    # S3 STORAGE MODE
    elif STORAGE_MODE == "s3":
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        file_name = f"qr_codes/{uuid.uuid4()}.png"

        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=file_name,
                Body=img_byte_arr,
                ContentType="image/png",
                ACL="public-read",
            )

            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
            return {
                "mode": "s3",
                "qr_code_url": s3_url
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=500, detail="Invalid STORAGE_MODE")
