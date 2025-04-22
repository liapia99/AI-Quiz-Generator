import os
import requests
from openai import OpenAI 
import replicate
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google.cloud import storage
import re
import uuid
# Load environment variables from .env file
load_dotenv()

  # Needed for session
# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create the folder if it doesn't exist

def upload_pdf_to_gcs(filepath):
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    filename = os.path.basename(filepath)

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(filepath)

        # Make the file public and return the public URL
        #blob.make_public()
        return blob.public_url

    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None
    
# Function to call Replicate API with the URL of the PDF file
def upload_pdf_to_replicate(file_url):
    output = replicate.run(
        "cuuupid/markitdown:dbaed480930eebcf09fbfeac1050a58af8600088058b5124a10988d1ff3432fd",
        input={
            "doc": file_url,
            "openai_api_key": os.getenv("OPENAI_API_KEY")
        }
    )
    return output  # This should return the processed text from Replicate

# Function to generate quiz based on the text
def generate_quiz(text, num_questions, question_type):
    prompt = (
    f"You are an expert quiz generator. Based strictly on the following academic content, generate {num_questions} "
    f"{question_type.lower()} questions. Do not include any information that is not explicitly mentioned in the content. "
    f"Do not invent or assume topics. Stick exactly to the material provided.\n\n"
    f"Content:\n{text}\n\n"
)

    if question_type.lower() == "multiple_choice":
        prompt += (
            "Format:\n"
            "Q1: [Question text]\n"
            "A. Option A\n"
            "B. Option B\n"
            "C. Option C\n"
            "D. Option D\n"
            "Correct Answer: [Letter]\n"
            "Explanation: [Academic rationale for the correct answer and a brief note on why the other options are incorrect]\n\n"
        )
    elif question_type.lower() == "true_false":
        prompt += (
            "Format:\n"
            "Q1: [Academic statement]\n"
            "Answer: True or False\n"
            "Explanation: [Concise academic justification for the answer, referencing the content when appropriate]\n\n"
        )
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
    )
    print("Prompt sent to OpenAI:\n", prompt)
    print("Raw response from OpenAI:\n", response.choices[0].message.content)
    return response.choices[0].message.content



def parse_quiz(text, question_type):
    questions = []
    raw_questions = re.split(r"\n(?=Q\d+:)", text)

    for q in raw_questions:
        if not q.strip(): continue
        entry = {"id": str(uuid.uuid4())}
        lines = q.strip().split("\n")
        entry["question"] = lines[0].split(":", 1)[1].strip()

        if question_type == "multiple_choice":
            options = [l for l in lines if re.match(r"^[A-D]\.", l)]
            entry["options"] = [(o[0], o[3:].strip()) for o in options]
            answer_line = next((l for l in lines if l.startswith("Correct Answer:")), None)
            entry["correct"] = answer_line.split(":")[1].strip() if answer_line else ""
        elif question_type == "true_false":
            answer_line = next((l for l in lines if l.startswith("Answer:")), None)
            entry["options"] = [("True", "True"), ("False", "False")]
            entry["correct"] = answer_line.split(":")[1].strip() if answer_line else ""

        questions.append(entry)

    return questions

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["pdf"]
        num_questions = int(request.form["num_questions"])
        question_type = request.form["question_type"]

        if file.filename.endswith(".pdf"):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(filepath)

            file_url = upload_pdf_to_gcs(filepath)
            if not file_url:
                return "Error: File upload to gcs failed."

            replicate_url = upload_pdf_to_replicate(file_url)
            
            response = requests.get(replicate_url)
            llm_text = response.text

            quiz_raw = generate_quiz(llm_text, num_questions, question_type)

            print("Replicate Output:\n", llm_text)
            parsed_quiz = parse_quiz(quiz_raw, question_type)  # ➤ implement this
            session["quiz"] = parsed_quiz  # Store quiz in session

            return redirect(url_for("take_quiz"))

    return render_template("index.html", quiz=None)

@app.route("/quiz", methods=["GET", "POST"])
def take_quiz():
    quiz = session.get("quiz", [])
    if request.method == "POST":
        user_answers = request.form.to_dict()
        for q in quiz:
            user_answer = user_answers.get(q["id"])
            q["user_answer"] = user_answer
            q["correct"] = (user_answer == q["correct"])
        return render_template("result.html", quiz=quiz)

    return render_template("quiz.html", quiz=quiz)



if __name__ == '__main__':
    app.run(debug=True)