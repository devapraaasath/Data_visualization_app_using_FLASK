from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import os
import uuid
from flask_cors import CORS 
from PIL import Image, ImageDraw, ImageFont
import shutil


app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

UPLOAD_FOLDER = "uploads"
IMAGE_FOLDER = "images"

ALLOWED_EXTENSIONS = {"csv", "xlsx"}
ALLOWED_IMAGE_EXTENSIONS = {"jpeg", "png", "gif", "jpg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["IMAGE_FOLDER"] = IMAGE_FOLDER

data_store = {}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Create sample placeholder images if they don't exist
def create_sample_placeholders():
    # Create a default placeholder for images
    placeholder_path = os.path.join(os.getcwd(), "images", "placeholder.png")
    if not os.path.exists(placeholder_path):
        img = Image.new('RGB', (200, 200), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((20, 90), "Image Not Found", fill=(255, 255, 255))
        img.save(placeholder_path)
    
    # Copy sample images if available in a samples directory, or create them
    sample_files = [
        {"name": "apple.png", "color": (255, 0, 0)},
        {"name": "banana.png", "color": (255, 255, 0)},
        {"name": "cherry.jpg", "color": (180, 0, 0)},
        {"name": "dog.png", "color": (150, 100, 50)},
        {"name": "cat.gif", "color": (100, 100, 100)}
    ]
    
    for sample in sample_files:
        file_path = os.path.join(os.getcwd(), "images", sample["name"])
        if not os.path.exists(file_path):
            # For non-GIF images
            if not sample["name"].endswith(".gif"):
                img = Image.new('RGB', (200, 200), color=sample["color"])
                d = ImageDraw.Draw(img)
                d.text((30, 90), sample["name"].split(".")[0].title(), fill=(255, 255, 255))
                img.save(file_path)
            else:
                # For GIF, create a simple static image as GIF
                # This is a simplification since creating animated GIFs is more complex
                frames = []
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
                
                for color in colors:
                    frame = Image.new('RGB', (200, 200), color=color)
                    d = ImageDraw.Draw(frame)
                    d.text((40, 90), "Animated GIF", fill=(255, 255, 255))
                    frames.append(frame)
                
                # Save as GIF
                frames[0].save(
                    file_path,
                    format='GIF',
                    append_images=frames[1:],
                    save_all=True,
                    duration=500,
                    loop=0
                )

create_sample_placeholders()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/')
def index():
    return "Flask is running"

@app.route('/upload', methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return jsonify({"message": "File saved successfully", "filename": filename}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400

@app.route('/process', methods=["POST"])
def process():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    if "filename" not in data:
        return jsonify({"error": "Filename not provided"}), 400

    filename = data["filename"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File does not exist"}), 400

    try:
        # For CSV files, explicitly convert column names to lowercase for consistency
        if filename.endswith(".csv"):
            df = pd.read_csv(filepath)
            # Convert column names to lowercase for consistency
            df.columns = [col.lower() for col in df.columns]
            # Look for standard image URL column names
            for col in df.columns:
                if 'image' in col.lower() or 'url' in col.lower() or 'img' in col.lower():
                    df.rename(columns={col: 'image_url'}, inplace=True)
                    break
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(filepath)
            # Convert column names to lowercase for consistency
            df.columns = [col.lower() for col in df.columns]
            # Look for standard image URL column names
            for col in df.columns:
                if 'image' in col.lower() or 'url' in col.lower() or 'img' in col.lower():
                    df.rename(columns={col: 'image_url'}, inplace=True)
                    break
        else:
            return jsonify({"error": "Unsupported file format"}), 400

        records = df.to_dict(orient="records")
        
        # Add fake sample images if there's no image_url column
        if 'image_url' not in df.columns:
            # Add sample images
            for i, record in enumerate(records):
                record['image_url'] = f"http://127.0.0.1:5000/get_image/sample{(i % 5) + 1}.jpg"
        else:
            # Format existing image URLs
            for record in records:
                if 'image_url' in record and record['image_url']:
                    # Ensure image URLs have http:// prefix
                    if not str(record['image_url']).startswith(('http://', 'https://')):
                        # Create proper URL format
                        image_filename = str(record['image_url']).split('/')[-1]
                        record['image_url'] = f"http://127.0.0.1:5000/get_image/{image_filename}"
        
        file_id = str(uuid.uuid4())
        data_store[file_id] = records
        
        return jsonify({"message": "Records stored successfully", "file_id": file_id, "data_preview": records[:5]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_data/<file_id>', methods=["GET"])
def get_data(file_id):
    if file_id not in data_store:
        return jsonify({"error": "Invalid file ID"}), 400

    return jsonify({"data": data_store[file_id]}), 200

@app.route('/get_file_image/<path:image_path>', methods=["GET"])
def get_file_image(image_path):
    """Serve an image from any path on the system"""
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 404

    try:
        mimetype = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mimetype = "image/png"
        elif image_path.lower().endswith(".gif"):
            mimetype = "image/gif"
        
        return send_file(image_path, mimetype=mimetype)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_image', methods=["POST"])
def upload_image():
    if "file_id" not in request.form:
        return jsonify({"error": "File ID not found"}), 400

    file_id = request.form["file_id"]

    if "image" not in request.files:
        return jsonify({"error": "No image found in the request"}), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({"error": "No selected image"}), 400

    if image and allowed_image(image.filename):
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["IMAGE_FOLDER"], f"{file_id}__{image_filename}")
        image.save(image_path)

        return jsonify({"message": "Image uploaded successfully", "image_url": f"http://127.0.0.1:5000/get_image/{file_id}__{image_filename}"
                        
                        }), 200

    else:
        return jsonify({"error": "Invalid image format"}), 400

@app.route('/get_image/<image_filename>', methods=["GET"])
def get_image(image_filename):
    image_path = os.path.join(os.getcwd(), "images", image_filename)

    # If the image doesn't exist, serve a placeholder
    if not os.path.exists(image_path):
        # Determine what type of placeholder to use based on extension
        if image_filename.lower().endswith('.gif'):
            gif_placeholder_path = os.path.join(os.getcwd(), "images", "cat.gif")
            if os.path.exists(gif_placeholder_path):
                return send_file(gif_placeholder_path, mimetype="image/gif")
            else:
                # If no GIF placeholder exists, use the general placeholder
                placeholder_path = os.path.join(os.getcwd(), "images", "placeholder.png")
                if os.path.exists(placeholder_path):
                    return send_file(placeholder_path, mimetype="image/png")
                else:
                    return jsonify({"error": "No placeholder image found"}), 404
        else:
            # For non-GIF images, use the static placeholder
            placeholder_path = os.path.join(os.getcwd(), "images", "placeholder.png")
            if os.path.exists(placeholder_path):
                return send_file(placeholder_path, mimetype="image/png")
            else:
                return jsonify({"error": "Image not found and no placeholder available"}), 404

    # For existing images, serve them with the proper mimetype
    mimetype = "image/jpeg"  # Default
    if image_filename.lower().endswith(".png"):
        mimetype = "image/png"
    elif image_filename.lower().endswith(".gif"):
        mimetype = "image/gif"

    return send_file(image_path, mimetype=mimetype)

@app.route('/search', methods=['POST'])
def search():
    """Search for records based on a query."""
    data = request.get_json()

    # Check if 'file_id' and 'query' are provided in the request
    if 'file_id' not in data or 'query' not in data:
        return jsonify({'error': 'file_id and query are required'}), 400

    file_id = data['file_id']
    query = data['query'].lower()  # Convert query to lowercase for case-insensitive search

    # Check if the file_id exists in the data_store
    if file_id not in data_store:
        return jsonify({'error': 'Invalid file_id'}), 400

    # Get the records for the file_id
    records = data_store[file_id]
    filtered_records = []

    # Iterate over the records and check if the query exists in any of the values
    for record in records:
        for value in record.values():
            if query in str(value).lower():  # Case-insensitive match
                filtered_records.append(record)
                break  # Once a match is found, no need to check further fields for this record

    # Return the filtered records
    return jsonify({'results': filtered_records}), 200

if __name__ == "__main__":
    app.run(debug=True)