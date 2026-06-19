import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from utils.utils import (
    extract_text_from_pdf,
    clean_text,
    rank_resumes
)

# -------------------------------
# APP CONFIG
# -------------------------------
app = Flask(__name__)
app.secret_key = "resume_screening_ai_secret"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_RESUMES = os.path.join(BASE_DIR, "static", "uploads", "resumes")
UPLOAD_JD = os.path.join(BASE_DIR, "static", "uploads", "job_descriptions")

ALLOWED_EXTENSIONS = {"pdf", "txt"}

os.makedirs(UPLOAD_RESUMES, exist_ok=True)
os.makedirs(UPLOAD_JD, exist_ok=True)

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    results = None

    if request.method == "POST":
        job_file = request.files.get("job_description")
        resume_files = request.files.getlist("resumes")

        if not job_file or job_file.filename == "":
            flash("Please upload a Job Description file.", "danger")
            return redirect(request.url)

        if not resume_files or resume_files[0].filename == "":
            flash("Please upload at least one resume.", "danger")
            return redirect(request.url)

        if not allowed_file(job_file.filename):
            flash("Job Description must be PDF or TXT.", "danger")
            return redirect(request.url)

        # ---- Save Job Description ----
        jd_filename = secure_filename(job_file.filename)
        jd_path = os.path.join(UPLOAD_JD, jd_filename)
        job_file.save(jd_path)

        # ---- Extract JD text ----
        if jd_filename.endswith(".pdf"):
            jd_text = extract_text_from_pdf(jd_path)
        else:
            jd_text = open(jd_path, encoding="utf-8", errors="ignore").read()

        jd_text = clean_text(jd_text)

        resume_texts = []
        resume_names = []

        # ---- Process Resumes ----
        for resume in resume_files:
            if resume and allowed_file(resume.filename):
                filename = secure_filename(resume.filename)
                path = os.path.join(UPLOAD_RESUMES, filename)
                resume.save(path)

                if filename.endswith(".pdf"):
                    text = extract_text_from_pdf(path)
                else:
                    text = open(path, encoding="utf-8", errors="ignore").read()

                resume_texts.append(clean_text(text))
                resume_names.append(filename)

        # ---- Rank Resumes ----
        results = rank_resumes(jd_text, resume_texts, resume_names)

    return render_template("dashboard.html", results=results)

@app.route("/load-sample")
def load_sample():
    SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample_resumes")

    # ---- Load Job Description ----
    jd_path = os.path.join(SAMPLE_DIR, "job_description.txt")
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = clean_text(f.read())

    resume_texts = []
    resume_names = []

    # ---- Load Sample Resumes ----
    for file in os.listdir(SAMPLE_DIR):
        if file.endswith(".txt") and file != "job_description.txt":
            path = os.path.join(SAMPLE_DIR, file)
            with open(path, encoding="utf-8", errors="ignore") as f:
                resume_texts.append(clean_text(f.read()))
                resume_names.append(file)

    results = rank_resumes(jd_text, resume_texts, resume_names)

    return render_template("dashboard.html", results=results)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")



# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
