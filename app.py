from flask import Flask, render_template, request, redirect, url_for
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
GOOGLE_DRIVE_FOLDER_ID = '1j83pj6sIL2mfNiWFqOYbb21vvNvlTwqd'

# Google Drive Auth
def get_gdrive_service():
    creds = None
    if os.path.exists('credentials/token.pickle'):
        with open('credentials/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json',
                ['https://www.googleapis.com/auth/drive.file']
            )
            creds = flow.run_local_server(port=0)
        
        with open('credentials/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['document']
        color_pages = request.form.get('color_pages', '')
        instructions = request.form.get('instructions', '')
        
        if file:
            # Save file locally
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Upload to Google Drive
            service = get_gdrive_service()
            file_metadata = {
                'name': filename,
                'parents': [GOOGLE_DRIVE_FOLDER_ID]
            }
            
            # Create text file with instructions
            instructions_filename = f"INSTRUCTIONS_{filename.split('.')[0]}.txt"
            instructions_content = f"Color pages: {color_pages}\nSpecial Instructions: {instructions}"
            
            # Upload both files
            for fname, content in [(file_path, None), (instructions_filename, instructions_content)]:
                media = MediaFileUpload(fname) if content is None else MediaIoBaseUpload(
                    io.BytesIO(content.encode()), mimetype='text/plain'
                )
                service.files().create(
                    body={'name': os.path.basename(fname), 'parents': [GOOGLE_DRIVE_FOLDER_ID]},
                    media_body=media,
                    fields='id'
                ).execute()
            
            os.remove(file_path)
            
            return redirect(url_for('success'))
    
    return render_template('index.html')

@app.route('/success')
def success():
    return "Order submitted successfully! We'll process your request shortly."

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(ssl_context='adhoc', debug=True)
