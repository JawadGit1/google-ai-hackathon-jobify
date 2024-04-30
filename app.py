from flask import Flask, render_template, request, redirect, send_file
import google.generativeai as genai
import os
import tempfile
import fitz  # PyMuPDF
import io
import base64
from jobapi import api
from docx import Document

app = Flask(__name__)

# Set up Gemini API key
os.environ['GOOGLE_API_KEY'] = "AIzaSyAf1LLRnbdhLZ8Mkih0iT69r98fpuCHaxU"
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                               generation_config=generation_config,
                               safety_settings=safety_settings)


# Convert PDF CV to images instead of OCR
def pdfcv_to_images(pdf_path):
    image_path_list = []

    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Iterate over each page
    for page_number in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_number)

        # Convert page to image
        resolution = 150
        pix = page.get_pixmap(matrix=fitz.Matrix(resolution/72, resolution/72))

        # Save the image
        image_path = tempfile.mktemp()
        pix._writeIMG(image_path, "png", 0)

        image_path_list.append(image_path)

    # Close the PDF
    pdf_document.close()
    return image_path_list


# Convert PIL image to base64 string
def pil_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


# Convert list of PIL images to base64 strings
def pil_images_to_base64(images):
    return [pil_to_base64(image) for image in images]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/interview')
def interview():
    return render_template('interview_form.html')


@app.route('/suggestion')
def suggestion():
    return render_template('suggestion_form.html')


@app.route('/search_jobs')
def search_jobs():
    return render_template('job_form.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        cv_file = request.files['cv_file']
        job_description = request.form['job_description']

        #save cv in temp file
        with tempfile.NamedTemporaryFile(delete=False) as temp_cv_file:
            cv_path = temp_cv_file.name
            cv_file.save(cv_path)

        #convert cv pdf to images
        images = pdfcv_to_images(cv_path)

        #get gemini response
        chat = model.start_chat()
        data_list = [
            """1. Here are my CV pictures and the job description I want to apply for.
            2. Please provide me with as many questions as possible that could be asked from me.
            3. make sure to give suggested answers according to my CV. Make should to ask Most important questions.
            4. Questions should be divided in portions like general questions, personality questions, Technical questions
            and brain storming questions""",
            *images[:5],  # Take at most the first 5 images
            "job description: ", job_description
        ]

        response = chat.send_message(data_list)
        response = response.text.replace("**", "").replace("* *", "").replace("*", "->")

        return render_template('interview.html', response=response)


@app.route('/get_cv_suggestion', methods=['POST'])
def get_suggestions():
    if request.method == 'POST':
        cv_file = request.files['cv_file']
        job_description = request.form['job_description']

        #save cv in temp file
        with tempfile.NamedTemporaryFile(delete=False) as temp_cv_file:
            cv_path = temp_cv_file.name
            cv_file.save(cv_path)

        #convert cv pdf to images
        images = pdfcv_to_images(cv_path)

        #get gemini response
        chat = model.start_chat()
        data_list = [
            """Here are my CV pictures and the job description I'm applying for.
            Review my cv and job description and tell me about my cv's
            Strenght, weaknesses and its solution. Like what keyword should I put in
            to get this job. Make sure to suggest revised form of cv.""",
            *images[:5],  # Take at most the first 5 images
            "job description: ", job_description
        ]

        response = chat.send_message(data_list)
        response = response.text.replace("**", "").replace("* *", "").replace("*", "->")

        return render_template('suggestion.html', response=response)


@app.route('/get_jobs', methods=['POST'])
def get_jobs():
    if request.method == 'POST':
        keyword = request.form['keyword']
        location = request.form['location']

        #get response from api, web scrapping of google jobs
        response = api.search_jobs(keyword, location)
        return render_template('jobs.html', jobs=response)


@app.route('/generate_doc', methods=['POST'])
def generate_word(): #function to generate .docx file
    text = request.form['text']
    doc = Document()
    doc.add_paragraph(text)
    with tempfile.NamedTemporaryFile(delete=False) as temp_doc_file:
        doc_path = temp_doc_file.name
        doc.save(doc_path)
    
    try: #online
        return send_file(doc_path, as_attachment=True, attachment_filename='output.docx',
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except: #local machine
        return send_file(doc_path, as_attachment=True, download_name='output.docx',
                         mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


if __name__ == "__main__":
    app.run()