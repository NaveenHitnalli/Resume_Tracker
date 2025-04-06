from flask import Flask, request, redirect, url_for, flash, render_template
import os
import mysql.connector
import re
from textblob import TextBlob
from werkzeug.utils import secure_filename
import PyPDF2

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Navee@03",
    database="resume_db"
)
cursor = conn.cursor()

# Ensure table exists
cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    skills TEXT,
                    ranking FLOAT
                )''')
conn.commit()

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract email from text
def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "unknown@example.com"

# Function to analyze resume and rank candidates
def analyze_resume(text):
    blob = TextBlob(text)
    skills = [word for word, tag in blob.tags if tag.startswith(('NN', 'VB', 'JJ'))]
    ranking = min(len(set(skills)) / 10.0, 10)  # Normalized ranking
    return ", ".join(set(skills)), ranking

# Homepage route
@app.route('/')
def index():
    cursor.execute("SELECT name, email, skills, ranking FROM resumes ORDER BY ranking DESC")
    resumes = cursor.fetchall()
    return render_template('index.html', resumes=resumes)

# Route to upload resume
@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file format. Please upload a PDF.')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    text = extract_text_from_pdf(file_path)
    email = extract_email(text)
    skills, ranking = analyze_resume(text)
    
    cursor.execute("INSERT INTO resumes (name, email, skills, ranking) VALUES (%s, %s, %s, %s)",
                   (filename, email, skills, ranking))
    conn.commit()
    flash('Resume uploaded and analyzed successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
