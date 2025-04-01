# Data Management and Visualization App

A web-based application that allows users to upload CSV/Excel files, view the data in a table format, and display images or GIFs associated with the data.

## Features

- Upload and parse CSV or Excel files
- Display data in a table format
- Show images and GIFs associated with records
- Search/filter functionality to find specific records
- Image replacement capability

## Setup and Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install flask pandas pillow flask-cors kivy werkzeug
```

3. Run the Flask backend:

```bash
cd flask_backend
python app.py
```

4. In a separate terminal, run the Kivy frontend:

```bash
cd flask_frontend
python main.py
```

## How to Use

### 1. Uploading CSV/Excel Files

1. Start both the Flask backend and Kivy frontend 
2. Use the file chooser to select a CSV or Excel file
3. Click the "Upload File" button
4. The data will be parsed and displayed in a table format

### 2. Working with Images and GIFs

#### CSV/Excel Format:

Your CSV or Excel file should include an `image_url` column containing:
- URLs to web-hosted images (starting with `http://` or `https://`)
- File names of locally stored images (app will serve them from `flask_backend/images/`)

Example CSV format:
```
id,name,description,image_url
1,Apple,Red fruit,http://example.com/apple.png
2,Banana,Yellow fruit,banana.png
```


#### For GIFs:

1. GIFs are supported and will animate in the interface
2. Make sure your GIFs are properly formatted
3. If a GIF doesn't display correctly, try setting `nocache=True` in the AsyncImage widget

#### Manually Adding Images:

To manually add images that can be referenced in your CSV:

1. Place your image files in the `flask_backend/images/` directory
2. In your CSV, reference them by filename in the `image_url` column (e.g., `cat.gif`)
3. Run the application and upload your CSV

