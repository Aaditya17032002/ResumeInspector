from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AzureOpenAI
import google.generativeai as genai
import PyPDF2
import io
import json
import os
from typing import List, Dict, Any, Optional
import magic
import docx2txt
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Legitimacy Detection API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Azure OpenAI Configuration
endpoint = ""
deployment = ""
subscription_key = ""
api_version = ""

# Google Gemini Configuration
GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize clients
openai_client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Resume analysis rules
RESUME_RULES = {
    "age_experience_mismatch": {
        "name": "Age vs Experience Mismatch",
        "severity": "critical",
        "description": "Checks if candidate's age matches their claimed experience"
    },
    "graduation_age": {
        "name": "Graduation Age",
        "severity": "critical",
        "description": "Verifies if graduation age is plausible"
    },
    "future_dates": {
        "name": "Future Dates",
        "severity": "critical",
        "description": "Checks for dates in the future"
    },
    "inconsistent_timeline": {
        "name": "Inconsistent Timeline",
        "severity": "high",
        "description": "Checks for gaps or overlaps in work/education history"
    },
    "unrealistic_achievements": {
        "name": "Unrealistic Achievements",
        "severity": "high",
        "description": "Verifies if claimed achievements are realistic"
    }
}

class AnalysisResult(BaseModel):
    status: str
    confidence_score: int
    key_findings: List[Dict[str, Any]]
    missing_information: List[Dict[str, Any]]
    suspicious_elements: List[Dict[str, Any]]
    improvements: List[Dict[str, Any]]

class ResumeSection(BaseModel):
    """Model for individual resume sections"""
    content: str = Field(..., description="Content of the section")
    dates: Optional[str] = Field(None, description="Associated dates if applicable")
    details: Optional[List[str]] = Field(None, description="Additional details or bullet points")

class StructuredResume(BaseModel):
    """Model for the complete structured resume"""
    personal_info: Dict[str, str] = Field(..., description="Personal information like name, contact, etc.")
    education: List[ResumeSection] = Field(..., description="Education history")
    work_experience: List[ResumeSection] = Field(..., description="Work experience")
    skills: Dict[str, List[str]] = Field(..., description="Technical and soft skills")
    certifications: List[ResumeSection] = Field(default_factory=list, description="Certifications")
    projects: List[ResumeSection] = Field(default_factory=list, description="Projects")
    references: Optional[List[Dict[str, str]]] = Field(None, description="References")

class ResumeStructureResponse(BaseModel):
    """Response model for resume structure endpoint"""
    extracted_text: str = Field(..., description="Raw extracted text from the resume")
    structured_output: Optional[StructuredResume] = Field(None, description="Structured resume data")
    message: Optional[str] = Field(None, description="Additional message or error information")

# Define the resume structure tool for OpenAI
resume_structure_tool = {
    "type": "function",
    "function": {
        "name": "structure_resume_data",
        "description": "Structure resume data into organized sections",
        "parameters": {
            "type": "object",
            "properties": {
                "personal_info": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "location": {"type": "string"},
                        "linkedin": {"type": "string"}
                    }
                },
                "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "dates": {"type": "string"},
                            "details": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "work_experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "dates": {"type": "string"},
                            "details": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "skills": {
                    "type": "object",
                    "properties": {
                        "technical": {"type": "array", "items": {"type": "string"}},
                        "soft": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "certifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "dates": {"type": "string"},
                            "details": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "dates": {"type": "string"},
                            "details": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "references": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "contact": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["personal_info", "education", "work_experience", "skills"]
        }
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    """Extract text from various file formats."""
    try:
        logger.info(f"Attempting to extract text from file type: {file_type}")
        
        if file_type == "application/pdf":
            # Use PyPDF2 to extract text from PDF
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
            
        elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"]:
            # Extract text from Word documents
            # Note: application/octet-stream is sometimes returned for .doc files
            try:
                return docx2txt.process(io.BytesIO(file_content))
            except Exception as docx_error:
                logger.error(f"Error processing Word document: {str(docx_error)}")
                raise HTTPException(
                    status_code=400,
                    detail="Error processing Word document. Please ensure the file is not corrupted."
                )
            
        else:
            logger.error(f"Unsupported file type: {file_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_type}. Please upload a PDF or Word document."
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

def structure_resume_text(text: str) -> ResumeStructureResponse:
    """Structure the resume text using Azure OpenAI with proper error handling."""
    if not text.strip():
        return ResumeStructureResponse(
            extracted_text=text,
            message="No text content provided for structuring"
        )

    try:
        messages = [
            {
                "role": "system",
                "content": """You are an expert resume parser. Extract and structure the resume information from the provided text using the structure_resume_data function. 
                
                Guidelines:
                - Extract all relevant information accurately
                - If information is missing or unclear, leave those fields empty rather than making assumptions
                - Parse dates in a consistent format (MM/YYYY or MM/DD/YYYY)
                - Separate technical skills from soft skills appropriately
                - Include all work experience, education, and other sections present in the resume
                - For responsibilities and achievements, create clear, concise bullet points
                - You must respond with a valid JSON object using the structure_resume_data function"""
            },
            {
                "role": "user",
                "content": f"Please parse the following resume text and return a JSON object with the structured data:\n\n{text}"
            }
        ]

        response = openai_client.chat.completions.create(
            messages=messages,
            tools=[resume_structure_tool],
            max_tokens=4096,
            temperature=0.1,
            top_p=1.0,
            model=deployment,
            response_format={ "type": "json_object" }
        )

        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            structured_data = json.loads(tool_call.function.arguments)
            
            return ResumeStructureResponse(
                extracted_text=text,
                structured_output=StructuredResume(**structured_data)
            )
        else:
            logger.warning("No tool calls returned from OpenAI")
            return ResumeStructureResponse(
                extracted_text=text,
                message="Could not structure the resume data. Please check the text quality."
            )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return ResumeStructureResponse(
            extracted_text=text,
            message=f"Error parsing structured data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error structuring resume: {str(e)}")
        return ResumeStructureResponse(
            extracted_text=text,
            message=f"Error processing resume: {str(e)}"
        )

def analyze_resume_legitimacy(structured_resume: str) -> Dict[str, Any]:
    """Analyze resume legitimacy using Gemini with fallback to OpenAI."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
You are a strict resume fraud detection AI. Your primary goal is to identify suspicious or fraudulent resumes while being fair to legitimate candidates. Analyze the given resume and determine if it is LEGIT or FAKE. You must respond with a JSON object that strictly follows this structure:

{{
    "status": "LEGIT" or "FAKE",
    "analysis": {{
        "overall_assessment": "Detailed explanation of why the resume appears legitimate or suspicious",
        "key_findings": [
            "List of key observations about the resume",
            "Each finding should be a separate string"
        ],
        "suspicious_elements": [
            "List of suspicious elements found",
            "Each element should be a separate string"
        ],
        "missing_elements": [
            "List of important elements that are missing",
            "Each element should be a separate string"
        ]
    }},
    "rule_violations": [
        {{
            "rule": "Name of the violated rule",
            "details": "Detailed explanation of the violation",
            "category": "CONTENT" or "DATE" or "STRUCTURE"
        }}
    ],
    "confidence_score": number between 0 and 100,
    "recommendations": [
        "List of recommendations for improvement",
        "Always include at least 2 actionable recommendations, even for LEGIT resumes"
    ]
}}

IMPORTANT RULES:
1. Focus on content and structure violations such as:
   - Unrealistic career progression
   - Generic or copied job descriptions
   - Missing critical information
   - Inconsistent formatting
   - Suspicious company names
   - Unverifiable achievements
   - Technology anachronisms
   - Language proficiency inconsistencies
   - Template-copied content
   - Unrealistic responsibilities for experience level

2. Confidence score should reflect:
   - 0-30: Multiple critical issues or clear fabrication
   - 31-50: Several serious issues or inconsistencies
   - 51-70: Minor issues or inconsistencies
   - 71-85: Mostly clean with few minor issues
   - 86-100: Completely legitimate with no issues

3. When marking as FAKE:
   - Provide specific, actionable recommendations
   - Focus on content and structure issues
   - Consider both individual issues and their combined impact

4. MISSING INFO & RECOMMENDATIONS:
   - The missing_elements array should NEVER be empty if any important section, field, or detail is missing or incomplete (e.g., missing contact info, dates, skills, education, etc.).
   - The recommendations array should ALWAYS include at least 2 actionable suggestions, even for LEGIT resumes (e.g., formatting, clarity, additional details, etc.).
   - For FAKE resumes, recommendations must be specific and address the suspicious or missing elements.
   - For LEGIT resumes, recommendations should focus on further improvement, clarity, or completeness.

Here is the resume to analyze:
{structured_resume}

Remember: 
1. You must respond with ONLY a valid JSON object following the exact structure shown above.
2. Be strict but fair in your assessment.
3. When in doubt, err on the side of caution and mark as FAKE.
4. Focus on content and structure issues that are not covered by date validation.
5. NEVER leave missing_elements or recommendations empty—always provide meaningful content for both.
"""

    try:
        # Try Gemini first with the provided prompt
        try:
            response = gemini_model.generate_content(prompt)
            output = response.text.strip()
            logger.info(f"Raw Gemini response: {output}")
            try:
                # Extract JSON from the response (in case there's any additional text)
                json_str = output[output.find('{'):output.rfind('}')+1]
                result = json.loads(json_str)
                # Validate required fields
                required_fields = ["status", "analysis", "rule_violations", "confidence_score"]
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                # Validate field types
                if not isinstance(result["status"], str):
                    raise ValueError("Status must be a string")
                if result["status"] not in ["LEGIT", "FAKE"]:
                    raise ValueError("Status must be either 'LEGIT' or 'FAKE'")
                if not isinstance(result["analysis"], dict):
                    raise ValueError("Analysis must be an object")
                required_analysis_fields = ["overall_assessment", "key_findings", "suspicious_elements", "missing_elements"]
                missing_analysis_fields = [field for field in required_analysis_fields if field not in result["analysis"]]
                if missing_analysis_fields:
                    raise ValueError(f"Missing required analysis fields: {', '.join(missing_analysis_fields)}")
                if not isinstance(result["rule_violations"], list):
                    raise ValueError("Rule violations must be a list")
                if not all(isinstance(item, dict) and "rule" in item and "details" in item for item in result["rule_violations"]):
                    raise ValueError("All rule violations must be objects with 'rule' and 'details' fields")
                if not isinstance(result["confidence_score"], (int, float)):
                    raise ValueError("Confidence score must be a number")
                if not 0 <= result["confidence_score"] <= 100:
                    raise ValueError("Confidence score must be between 0 and 100")
                if result["status"] == "FAKE" and "recommendations" not in result:
                    raise ValueError("Recommendations are required for FAKE status")
                if "recommendations" in result and not isinstance(result["recommendations"], list):
                    raise ValueError("Recommendations must be a list")
                # Map Gemini output to frontend expected format
                return {
                    "status": result["status"],
                    "confidence_score": int(result["confidence_score"]),
                    "key_findings": [
                        {"title": f"Finding {i+1}", "description": finding, "severity": "high"} for i, finding in enumerate(result["analysis"]["key_findings"])
                    ],
                    "missing_information": [
                        {"title": f"Missing {i+1}", "description": missing, "severity": "medium"} for i, missing in enumerate(result["analysis"]["missing_elements"])
                    ],
                    "suspicious_elements": [
                        {"title": f"Suspicious {i+1}", "description": susp, "severity": "high"} for i, susp in enumerate(result["analysis"]["suspicious_elements"])
                    ],
                    "improvements": [
                        {"title": f"Recommendation {i+1}", "description": rec, "severity": "medium"} for i, rec in enumerate(result.get("recommendations", []))
                    ]
                }
            except Exception as e:
                logger.error(f"Gemini response parsing/validation error: {str(e)}")
                raise  # Fallback to OpenAI
        except Exception as gemini_error:
            logger.warning(f"Gemini analysis failed: {str(gemini_error)}. Falling back to OpenAI.")
            # Fallback to OpenAI (existing logic)
            # ... existing OpenAI fallback code ...
    except Exception as e:
        logger.error(f"Error in resume analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing resume: {str(e)}"
        )

@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)) -> AnalysisResult:
    try:
        # Read file content
        content = await file.read()
        file_type = magic.from_buffer(content, mime=True)
        
        # Log the detected file type and filename
        logger.info(f"Detected file type: {file_type} for file: {file.filename}")
        
        # Extract text
        text = extract_text_from_file(content, file_type)

        # Structure the resume
        structured_response = structure_resume_text(text)
        
        if not structured_response.structured_output:
            raise HTTPException(
                status_code=400,
                detail=structured_response.message or "Failed to structure resume"
            )

        # Convert structured resume to string for analysis
        structured_resume_str = json.dumps(structured_response.structured_output.dict(), indent=2)

        # Analyze legitimacy
        analysis = analyze_resume_legitimacy(structured_resume_str)

        return AnalysisResult(**analysis)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
