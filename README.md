# AI-Quiz-Generator

An intelligent web application that automatically generates quizzes from PDF documents using AI technology. The application processes academic content and creates customized quizzes with multiple-choice or true/false questions.

## Features

- PDF document processing
- Automatic quiz generation using GPT-4
- Support for multiple-choice and true/false questions
- Interactive quiz interface
- Immediate feedback and scoring
- Cloud storage integration for document processing

## Technical Stack

- **Backend**: Python Flask
- **AI/ML**: 
  - OpenAI GPT-4 for quiz generation
  - Replicate API for PDF processing
- **Cloud Storage**: Google Cloud Storage
- **Frontend**: HTML/CSS with Flask templates

## Prerequisites
- Python 3.x
- OpenAI API key
- Google Cloud Storage credentials
- Replicate API access

## Required Accounts
### 1. OpenAI Account
- Create an account at [OpenAI Platform](https://platform.openai.com/signup)
- Navigate to API keys section
- Generate a new API key
- Note: OpenAI API usage requires a paid account with billing information - I did 5 dollars. 

### 2. Google Cloud Account
- Create a Google Cloud account at [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable Cloud Storage API
- Create a service account and download credentials JSON file
- Create a storage bucket and note its name
- Set up billing information (required for API access) - You need to add a credit card but you don't have to pay anything unless you want to make the project bigger. We are just testing it for now. 

### 3. Replicate Account
- Sign up at [Replicate](https://replicate.com/)
- Get your API token from account settings
- Note: Some API usage may require billing information - This one does. I just did 2 dollars. 

## Environment Variables

Create a `.env` file with the following variables:
```
FLASK_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=our_gcs_app_credentials
GCS_BUCKET_NAME=your_gcs_bucket_name
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install flask openai replicate google-cloud-storage python-dotenv
   ```
3. Set up your environment variables
4. Run the application:
   ```bash
   python app.py
   ```

## Usage

1. Access the web application at `http://localhost:5000`
2. Upload a PDF document containing academic content
3. Select the number of questions and question type (multiple-choice or true/false)
4. Submit the document for processing
5. Take the generated quiz
6. View your results and explanations

## Project Structure

```
├── app.py             # Main Flask application
├── templates/         # HTML templates
│   ├── index.html     # Upload page
│   ├── quiz.html      # Quiz interface
│   └── result.html    # Results page
├── static/            # Static assets
└── uploads/           # Temporary PDF storage
```

## How It Works

1. **Document Processing**:
   - User uploads a PDF file
   - File is stored in Google Cloud Storage
   - PDF is processed using Replicate's markitdown model

2. **Quiz Generation**:
   - Processed text is sent to GPT-4
   - AI generates questions based on content
   - Questions are formatted and parsed

3. **Quiz Interface**:
   - Users can take the generated quiz
   - Immediate feedback on answers
   - Detailed explanations provided

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Images
<img width="1440" alt="Screenshot 2025-04-30 at 4 04 58 AM" src="https://github.com/user-attachments/assets/473d39a7-2040-44c1-875b-25728d25c45b" />
<img width="1440" alt="Screenshot 2025-04-30 at 4 05 20 AM" src="https://github.com/user-attachments/assets/a1a9cdf5-88a5-4b9b-bb8c-dbb036c4ff66" />
<img width="1440" alt="Screenshot 2025-04-30 at 4 05 33 AM" src="https://github.com/user-attachments/assets/b4f4c14d-e89e-42b4-a3e9-39496b527aa9" />
<img width="1440" alt="Screenshot 2025-04-30 at 4 04 36 AM" src="https://github.com/user-attachments/assets/748699af-e8f0-477a-85e9-57bcd024d8b7" />
