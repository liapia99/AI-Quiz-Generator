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


# load environment variables from .env file
load_dotenv()


# initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # create the 'uploads' folder if it doesn't exist


# have to upload the user's pdf to google cloud storage
def upload_pdf_to_gcs(filepath):
    bucket_name = os.getenv("GCS_BUCKET_NAME") #getting gcs bucket (in the .env file)
    filename = os.path.basename(filepath)

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(filepath) # uploads the user's pdf to gcs as a blob in the bucket

        return blob.public_url

    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None
    


# call replicate model via api with the url of the pdf file
def upload_pdf_to_replicate(file_url):
    output = replicate.run(
        "cuuupid/markitdown:dbaed480930eebcf09fbfeac1050a58af8600088058b5124a10988d1ff3432fd", # the replicate model we are using
        input={
            "doc": file_url,
            "openai_api_key": os.getenv("OPENAI_API_KEY")
        }
    )
    # this replicate model converts pdfs into LLM-ready markdown text 
    return output  # return the processed text from replicate so it can go to openai

# generate quiz based on the replicate text
def generate_quiz(text, num_questions, question_type):
    # have to give prompt to openai gpt-4 model so it knows what to do with the replicate text
    prompt = (
    f"You are an expert quiz generator. Based strictly on the following academic content, generate {num_questions} "
    f"{question_type.lower()} questions. Do not include any information that is not explicitly mentioned in the content. "
    f"Do not invent or assume topics. Stick exactly to the material provided.\n\n"
    f"Content:\n{text}\n\n"
)
    # format of the multiple choice questions
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
        # format for true/false questions
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
    # debugging in terminal - print out what is given by replicate and openai
    print("Prompt sent to OpenAI:\n", prompt)
    print("Raw response from OpenAI:\n", response.choices[0].message.content)
    return response.choices[0].message.content


# text generated from openai to quiz format
def parse_quiz(text, question_type):
    # empty list for the questions created by openai
    questions = []
    raw_questions = re.split(r"\n(?=Q\d+:)", text)

    for q in raw_questions:
        if not q.strip():
            continue
        # creates a dictionary to store one question’s data
        entry = {"id": str(uuid.uuid4()), "user_answer": None}  # initialize user_answer
        lines = q.strip().split("\n")

        # gets actual question text by splitting on the first colon (`Q1: ...`) and trimming it
        entry["question"] = lines[0].split(":", 1)[1].strip()

        # builds a list of tuples 
        if question_type == "multiple_choice":
            options = [l for l in lines if re.match(r"^[A-D]\.", l)]
            entry["options"] = [(o[0], o[3:].strip()) for o in options]
            answer_line = next((l for l in lines if l.startswith("Correct Answer:")), None)
            entry["correct"] = answer_line.split(":")[1].strip() if answer_line else ""
            explanation_line = next((l for l in lines if l.startswith("Explanation:")), None)
            entry["explanation"] = explanation_line.split(":", 1)[1].strip() if explanation_line else ""

        elif question_type == "true_false":
            answer_line = next((l for l in lines if l.startswith("Answer:")), None)
            entry["options"] = [("True", "True"), ("False", "False")]
            entry["correct"] = answer_line.split(":")[1].strip() if answer_line else ""
            explanation_line = next((l for l in lines if l.startswith("Explanation:")), None)
            entry["explanation"] = explanation_line.split(":", 1)[1].strip() if explanation_line else ""
        # adds the full question to the list
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
            parsed_quiz = parse_quiz(quiz_raw, question_type)  
            session["quiz"] = parsed_quiz  # store quiz in session

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
            q["is_correct"] = (user_answer == q["correct"])

        # calculate after assigning user_answer
        correct_count = sum(1 for q in quiz if q["is_correct"])
        total_count = len(quiz)

        return render_template("result.html", quiz=quiz, correct_count=correct_count, total_count=total_count)

    return render_template("quiz.html", quiz=quiz)



if __name__ == '__main__':
    app.run(debug=True)
