import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PyPDF2 import PdfReader
import pandas as pd

# Download stopwords once
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")


# -------------------------------
# TEXT CLEANING
# -------------------------------
def clean_text(text: str) -> str:
    """
    Clean and normalize text:
    - lowercase
    - remove special characters & numbers
    - remove stopwords
    """
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)

    words = text.split()
    stop_words = set(stopwords.words("english"))

    cleaned_words = [w for w in words if w not in stop_words and len(w) > 2]
    return " ".join(cleaned_words)


# -------------------------------
# PDF TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from PDF file
    """
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + " "

    return text


# -------------------------------
# RESUME RANKING LOGIC
# -------------------------------
def rank_resumes(job_description: str, resumes: list, resume_names: list):
    """
    Rank resumes based on cosine similarity with job description
    """
    documents = [job_description] + resumes

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    results = []
    for name, score in zip(resume_names, similarity_scores):
        results.append({
            "resume": name,
            "score": round(score * 100, 2)
        })

    # Sort by score (highest first)
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return pd.DataFrame(results)

