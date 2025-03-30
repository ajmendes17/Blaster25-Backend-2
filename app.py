from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
# import io
import os
import openai
import base64
# import pprint
# import asyncio
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

MODEL_NAME = "llama-3.2-90b-vision-preview"
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def prompting(subject, words):

    # Check if the list of words is not empty
    if words:
        # Use an f-string to format the prompt
        return f"Solve this {subject} problem related to these topics: {', '.join(words)}"
    else:
        # If the list of words is empty, return a different prompt
        return f"Solve this {subject} problem"
 
        

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config = {
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
    'ALLOWED_EXTENSIONS': {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
}

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def parse_latex(latex_text):
    return latex_text.split("```latex")[1].split("```")[0]


async def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



@app.post("/uploads")
async def upload_file(file: UploadFile = File(...), prompt: str = ...):
    try:
        if not file or not prompt:
            raise HTTPException(status_code=400, detail="No file or prompt provided")

        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Save prompt
        prompt_path = os.path.join(app.config['UPLOAD_FOLDER'], "prompt.txt")
        with open(prompt_path, "w") as f:
            f.write(prompt)

        # Read prompt
        prompt_path = os.path.join(app.config['UPLOAD_FOLDER'], "prompt.txt")
        with open(prompt_path, "r") as f:
            prompt = f.read()

        # Read image
       

        # Extract text using Tesseract
        # image = Image.open(image_path)
        # extracted_text = pytesseract.image_to_string(image)
        # if not extracted_text:
        #     raise HTTPException(status_code=400, detail="No text extracted from image")

        # Encode image to Base64
        logger.info(file_path)
        # image_path = "uploads/TEST.png"
        base64_image = await encode_image(file_path)

        # Prepare prompt, add inputs for prompting
        full_prompt = prompting() + f""" 
        You must return all the LaTeX code for the given image provided. Output all of the code.

        #Important Rules:
        You MUST start your latex code with ```latex and end with ```.
        You must include
        \\documentclass{{article}}
        \\begin{{document}}
        The User's prompt is as follows:
        {prompt}
        """

        # Call Groq API
        client = openai.OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        # return {"status": "success", "latex_code": base64_image}
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
        )

        if not completion or not completion.choices:
            raise HTTPException(status_code=500, detail="No response from Groq API")

        latex_code = parse_latex(completion.choices[0].message.content)
        return {"status": "success", "latex_code": latex_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/process")
async def process_file():
    try:
        # Read prompt
        prompt_path = os.path.join(app.config['UPLOAD_FOLDER'], "prompt.txt")
        with open(prompt_path, "r") as f:
            prompt = f.read()

        # Read image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.listdir(app.config['UPLOAD_FOLDER'])[0])
        if not image_path:
            raise HTTPException(status_code=400, detail="No image found")

        # Extract text using Tesseract
        # image = Image.open(image_path)
        # extracted_text = pytesseract.image_to_string(image)
        # if not extracted_text:
        #     raise HTTPException(status_code=400, detail="No text extracted from image")

        # Encode image to Base64
        base64_image = await encode_image(image_path)

        # Prepare prompt
        full_prompt = f"""
        You must return all the LaTeX code for the given image provided. Output all of the code.

        #Important Rules:
        You MUST start your latex code with ```latex and end with ```.
        You must include
        \\documentclass{{article}}
        \\begin{{document}}
        The User's prompt is as follows:
        {prompt}
        """

        # Call Groq API
        client = openai.OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )

        completion = await client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
        )

        if not completion or not completion.choices:
            raise HTTPException(status_code=500, detail="No response from Groq API")

        latex_code = parse_latex(completion.choices[0].message.content)
        return {"status": "success", "latex_code": latex_code}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    

@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3001, reload=True)