from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import PyPDF2
import docx
import re
import json
import io
import requests
import base64
from fastapi.responses import JSONResponse
import gdown

# Root directory and environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ResumeAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resume_text: str
    roast: str
    review: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResumeResponse(BaseModel):
    id: str
    roast: str
    review: str
    timestamp: datetime

# Helper functions for resume processing

def extract_text_from_pdf(file_content):
    """Extract text from PDF file content."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_content):
    """Extract text from DOCX file content."""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
        return None

def extract_text_from_gdrive_link(gdrive_link):
    """Extract text from Google Drive document."""
    try:
        # Extract the file ID from the Google Drive link
        file_id_match = re.search(r"(?:\/d\/|id=)([a-zA-Z0-9_-]+)", gdrive_link)
        if not file_id_match:
            return None
        
        file_id = file_id_match.group(1)
        
        # Create a temporary file to store the downloaded document
        temp_file = f"/tmp/{uuid.uuid4()}"
        
        # Download the file from Google Drive
        gdown.download(f"https://drive.google.com/uc?id={file_id}", temp_file, quiet=True)
        
        # Determine file type and extract text
        if os.path.exists(temp_file):
            with open(temp_file, 'rb') as f:
                file_content = f.read()
                
            # Try to determine file type and extract text accordingly
            try:
                text = extract_text_from_pdf(file_content)
                if text:
                    return text
            except:
                pass
                
            try:
                text = extract_text_from_docx(file_content)
                if text:
                    return text
            except:
                pass
                
            # Clean up
            os.remove(temp_file)
            
        return None
    except Exception as e:
        logging.error(f"Error extracting text from Google Drive link: {e}")
        return None

def generate_roast_and_review(resume_text):
    """Generate a humorous roast and a serious review of the resume using HuggingFace API."""
    try:
        # Use a publicly available model from HuggingFace for text generation
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # Prepare the prompt for roasting
        roast_prompt = f"""
        Below is a resume content:
        ---
        {resume_text[:3000]}  # Limiting text length to avoid token limits
        ---
        
        Create a humorous and sarcastic "roast" of this resume, pointing out potential inconsistencies, 
        exaggerations, or generic elements in a funny way. Keep it light-hearted but witty.
        """
        
        # Prepare the prompt for constructive review
        review_prompt = f"""
        Below is a resume content:
        ---
        {resume_text[:3000]}  # Limiting text length to avoid token limits
        ---
        
        Provide a professional and constructive review of this resume. 
        Highlight strengths, suggest improvements, and offer specific advice on how to make it more effective.
        """
        
        # Function to call the Hugging Face Inference API
        def query_huggingface(payload):
            response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
            return response.json()
            
        # Get the roast
        roast_response = query_huggingface({"inputs": roast_prompt, "parameters": {"max_length": 500}})
        roast = roast_response[0]["generated_text"] if isinstance(roast_response, list) else "Failed to generate roast. The AI is probably too impressed with your resume to find anything to joke about!"
        
        if isinstance(roast, str) and roast.startswith(roast_prompt):
            roast = roast[len(roast_prompt):].strip()
        
        # Get the review
        review_response = query_huggingface({"inputs": review_prompt, "parameters": {"max_length": 500}})
        review = review_response[0]["generated_text"] if isinstance(review_response, list) else "Failed to generate review. Your resume is beyond conventional analysis!"
        
        if isinstance(review, str) and review.startswith(review_prompt):
            review = review[len(review_prompt):].strip()
        
        return roast, review
        
    except Exception as e:
        logging.error(f"Error generating roast and review: {e}")
        # Provide fallback responses
        roast = "I tried to roast your resume, but my AI brain is too fried right now. Maybe your resume is just too hot to handle!"
        review = "I wanted to give you a proper review, but something went wrong. Your resume is probably breaking new ground that AI can't comprehend yet!"
        return roast, review

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Resume Roaster API is running"}

@api_router.post("/upload-resume")
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    gdrive_link: Optional[str] = Form(None)
):
    """Upload and analyze a resume."""
    try:
        resume_text = None
        
        # Process file upload
        if file:
            file_content = await file.read()
            filename = file.filename.lower()
            
            if filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_content)
            elif filename.endswith('.docx'):
                resume_text = extract_text_from_docx(file_content)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or DOCX file.")
        
        # Process Google Drive link
        elif gdrive_link:
            resume_text = extract_text_from_gdrive_link(gdrive_link)
            if not resume_text:
                raise HTTPException(status_code=400, detail="Failed to extract text from Google Drive link. Please ensure it's a PDF or DOCX file and is publicly accessible.")
        
        else:
            raise HTTPException(status_code=400, detail="No file or Google Drive link provided")
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from the document")
        
        # Generate roast and review using LLM
        roast, review = generate_roast_and_review(resume_text)
        
        # Save to database
        resume_analysis = ResumeAnalysis(
            resume_text=resume_text,
            roast=roast,
            review=review
        )
        
        result = await db.resume_analyses.insert_one(resume_analysis.dict())
        
        # Return response
        return ResumeResponse(
            id=resume_analysis.id,
            roast=roast,
            review=review,
            timestamp=resume_analysis.timestamp
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error processing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
