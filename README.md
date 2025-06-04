# ResumeInspector

ResumeInspector is a FastAPI-based web application for analyzing and detecting the legitimacy of resumes using Azure OpenAI and Google Gemini models. It extracts, structures, and evaluates resume content for potential fraud, missing information, and improvement suggestions.

## Features
- Upload and analyze PDF or Word resumes
- AI-powered structuring and legitimacy analysis
- Detects suspicious elements, missing info, and provides actionable recommendations
- Web interface and REST API endpoints

## Requirements
- Python 3.8+
- See `requirements.txt` for all dependencies

## Environment Variables
Create a `.env` file in the project root (see `.env.example`):

```
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment_name
AZURE_OPENAI_SUBSCRIPTION_KEY=your_azure_openai_key
AZURE_OPENAI_API_VERSION=your_azure_openai_api_version
GOOGLE_API_KEY=your_google_gemini_api_key
```

## Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/Aaditya17032002/ResumeInspector.git
   cd ResumeInspector
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your keys.

## Running the Application
Start the FastAPI server with Uvicorn:

```sh
uvicorn app:app --reload
```

- The app will be available at [http://localhost:8000](http://localhost:8000)
- The root endpoint (`/`) serves the web interface (if `templates/index.html` exists)
- The `/analyze` endpoint accepts resume file uploads (PDF/DOCX)

## Example .env File
See `.env.example` for the required variables.

## Project Structure
```
ResumeInspector/
├── app.py
├── requirements.txt
├── .env.example
├── templates/
├── static/
└── ...
```

## Notes
- **Never commit your real API keys or secrets to the repository.**
- For production, remove `--reload` from the Uvicorn command.
- If you change environment variables, restart the server.

## License
MIT
