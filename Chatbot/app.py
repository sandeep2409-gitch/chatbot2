from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename 


load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def format_text(text: str) -> str:
    """
    Convert plain/AI text into HTML:
    - Paragraphs (<p>)
    - Bullet lists (<ul><b><li>)
    - Line breaks

    """
    if not text:
        return ""

    lines = text.split("\n")
    formatted = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith(("-", "º")):
            if not in_list:
                formatted.append("<ul>")
                in_list = True
            formatted.append(f"<li>{stripped[1:].strip()}</li>")
        else:
            if in_list:
                formatted.append("</ul>")
                in_list = False
            if stripped:
                formatted.append(f"<p>{stripped}</p>")

    if in_list:
        formatted.append("</ul>")

    return "".join(formatted)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"response": "⚠️ No message received."})

    try:
        response = model.generate_content(user_message)
        bot_reply = response.text if response and response.text else "⚠️ No response from AI."
        return jsonify({"response": format_text(bot_reply)})
    except Exception as e:
        return jsonify({"response": f"⚠️ Error: {str(e)}"})


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"response": "⚠️ No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"response": "⚠️ No file selected."}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
     
        if filename.lower().endswith((".txt", ".md")):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            response = model.generate_content(f"Summarize this file:\n{content[:5000]}")
            bot_reply = response.text if response and response.text else "File received but no summary."
        else:
            bot_reply = f"📎 File '{filename}' uploaded successfully!"
    except Exception as e:
        bot_reply = f"⚠️ File uploaded but error reading content: {str(e)}"

    return jsonify({"response": format_text(bot_reply)})



if __name__ == "__main__":
    app.run(debug=True)