import os
import pickle
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

app = Flask(__name__)

# Path to token.pickle
TOKEN_PICKLE_PATH = 'token.pickle'

# Folder ID where files will be uploaded
FOLDER_ID = '1j83pj6sIL2mfNiWFqOYbb21vvNvlTwqd'  # Replace with your actual Google Drive folder ID

def get_drive_service():
    """Authenticate and return the Google Drive service."""
    creds = None
    # Load the token.pickle file
    if os.path.exists(TOKEN_PICKLE_PATH):
        with open(TOKEN_PICKLE_PATH, 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials are available, raise an error
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("No valid credentials found. Please generate token.pickle.")
    # Build the Drive service
    return build('drive', 'v3', credentials=creds)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload requests."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the file temporarily
    file_path = os.path.join('/tmp', file.filename)
    file.save(file_path)

    try:
        # Authenticate and get the Drive service
        drive_service = get_drive_service()

        # File metadata including the parent folder ID
        file_metadata = {
            'name': file.filename,
            'parents': [FOLDER_ID]  # Specify the folder ID here
        }

        # Create a media object for the file
        media = MediaFileUpload(file_path, resumable=True)

        # Upload the file
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # Clean up the temporary file
        os.remove(file_path)

        return jsonify({
            'message': 'File uploaded successfully!',
            'file_id': uploaded_file.get('id')
        }), 200

    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
