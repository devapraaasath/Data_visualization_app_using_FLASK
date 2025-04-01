from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import os
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# File settings
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup folders
UPLOAD_FOLDER = "uploads"
IMAGE_FOLDER = "images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# File type settings
ALLOWED_FILES = {".csv", ".xlsx"}
ALLOWED_IMAGES = {".jpeg", ".png", ".gif", ".jpg"}

# Store uploaded data in memory
data_storage = {}

def is_valid_file(filename, allowed_types):
    """Check if file has an allowed extension"""
    return os.path.splitext(filename)[1].lower() in allowed_types

def find_image_column(df):
    """Find column that might contain image URLs"""
    for col in df.columns:
        if any(word in col.lower() for word in ['image', 'url', 'img']):
            return col
    return None

def format_image_url(url):
    """Format image URL to ensure proper structure"""
    if not url or not isinstance(url, str):
        return url
    if url.startswith(('http://', 'https://')):
        return url
    return f"http://127.0.0.1:5000/get_image/{url.split('/')[-1]}"

def process_dataframe(df):
    """Process dataframe to standardize column names and handle image URLs"""
    # Convert columns to lowercase
    df.columns = df.columns.str.lower()
    
    # Handle image column
    image_col = find_image_column(df)
    if image_col:
        df.rename(columns={image_col: 'image_url'}, inplace=True)
        df['image_url'] = df['image_url'].apply(format_image_url)
    else:
        # Add sample images if no image column exists
        df['image_url'] = [f"http://127.0.0.1:5000/get_image/sample{(i % 5) + 1}.jpg" 
                          for i in range(len(df))]
    
    return df

@app.route('/')
def home():
    return "Server is running"

@app.route('/upload', methods=["POST"])
def upload_file():
    # Check if file was sent
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Validate file type
    if not is_valid_file(file.filename, ALLOWED_FILES):
        return jsonify({"error": "Invalid file type. Please upload CSV or Excel file"}), 400

    # Save file safely
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return jsonify({
        "message": "File uploaded successfully",
        "filename": filename
    }), 200

@app.route('/process', methods=["POST"])
def process_file():
    data = request.get_json()
    if not data or "filename" not in data:
        return jsonify({"error": "No filename provided"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, data["filename"])
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        # Read file based on type
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        if df.empty:
            return jsonify({"message": "File is empty"}), 200
            
        # Process the data
        df = process_dataframe(df)
        records = df.to_dict(orient="records")
        
        # Store with unique ID
        file_id = str(uuid.uuid4())
        data_storage[file_id] = records
        
        return jsonify({
            "message": "File processed successfully",
            "file_id": file_id,
            "preview": records[:5]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/get_data/<file_id>')
def get_data(file_id):
    if file_id not in data_storage:
        return jsonify({"data": []}), 200  # Return empty list instead of error
    return jsonify({"data": data_storage[file_id]}), 200

@app.route('/search', methods=['POST'])
def search_data():
    data = request.get_json()
    if not data or 'file_id' not in data or 'query' not in data:
        return jsonify({"error": "Missing file_id or query"}), 400

    # Check if data exists
    file_id = data['file_id']
    if file_id not in data_storage:
        return jsonify({"results": []}), 200  # Return empty results instead of error

    # Search through records
    query = data['query'].lower()
    results = [
        record for record in data_storage[file_id]
        if any(query in str(value).lower() for value in record.values())
    ]

    return jsonify({"results": results}), 200

@app.route('/upload_image', methods=["POST"])
def upload_image():
    # Validate request
    if "file_id" not in request.form:
        return jsonify({"error": "No file ID provided"}), 400
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file_id = request.form["file_id"]
    image = request.files["image"]
    
    if not image.filename:
        return jsonify({"error": "No image selected"}), 400
    if not is_valid_file(image.filename, ALLOWED_IMAGES):
        return jsonify({"error": "Invalid image format"}), 400

    # Save image with unique name
    filename = f"{file_id}__{secure_filename(image.filename)}"
    image.save(os.path.join(IMAGE_FOLDER, filename))
    
    return jsonify({
        "message": "Image uploaded successfully",
        "image_url": f"http://127.0.0.1:5000/get_image/{filename}"
    }), 200

@app.route('/get_image/<filename>')
def get_image(filename):
    image_path = os.path.join(os.getcwd(), IMAGE_FOLDER, filename)
    
    # Handle missing images
    if not os.path.exists(image_path):
        # Use appropriate placeholder based on file type
        if filename.lower().endswith('.gif'):
            placeholder = os.path.join(os.getcwd(), IMAGE_FOLDER, "cat.gif")
            if os.path.exists(placeholder):
                return send_file(placeholder, mimetype="image/gif")
        
        # Default placeholder
        placeholder = os.path.join(os.getcwd(), IMAGE_FOLDER, "placeholder.png")
        if os.path.exists(placeholder):
            return send_file(placeholder, mimetype="image/png")
        return jsonify({"error": "Image not found"}), 404

    # Determine correct mimetype
    if filename.lower().endswith(".png"):
        mimetype = "image/png"
    elif filename.lower().endswith(".gif"):
        mimetype = "image/gif"
    else:
        mimetype = "image/jpeg"

    return send_file(image_path, mimetype=mimetype)

if __name__ == "__main__":
    app.run(debug=True)