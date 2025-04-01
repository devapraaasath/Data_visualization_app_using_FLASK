import requests

url = "http://127.0.0.1:5000/upload"
file_path = "sample.csv"  # Make sure this file exists in the same directory

with open(file_path, "rb") as file:
    files = {"file": file}  # Ensure the key is "file"
    response = requests.post(url, files=files)

print(response.json())  # Print response from Flask

