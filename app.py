from flask import Flask, request, render_template_string
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
import requests
import os

app = Flask(__name__)

# ✅ Secure Setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'googlecredentialsfile.json') #your json file path here
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1E1qSDQsKYztl7_2HuVvyrjWbHqJh-ReO') #your folder ID here
UPLOAD_WEBHOOK_URL = os.getenv('DISCORD_UPLOAD_WEBHOOK_URL', 'XXXXXXXXXXXXXXXX') #your discord webhook URL for Upload Channel
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx') #your discord bot token here

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

UPLOAD_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>📤 Multi-File Uploader</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background-color: #f5f5f5; }
        h2 { color: #333; }
        button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 5px; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <h2>📤 Upload Your Files</h2>
    <p> You can upload multiple files at a time</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="hidden" name="uploader_id" value="{{ uploader_id }}">
        <input type="hidden" name="channel_id" value="{{ channel_id }}">
        <input type="file" name="files" multiple required><br><br>
        <button type="submit">Upload</button>
    </form>
    <p>Made with ❤️ by Hasnain </p>
</body>
</html>
"""

def send_bot_message(channel_id, content):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"content": content}
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending bot message: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    uploader_id = request.args.get('uploader_id', '')
    channel_id = request.args.get('channel_id', '')

    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or not uploader_id or not channel_id:
            return "❌ Missing uploader ID, channel ID, or files."
        
        uploaded_links = []
        try:
            for file in files:
                temp_path = f"/tmp/{file.filename}"
                file.save(temp_path)
                
                file_metadata = {'name': file.filename, 'parents': [FOLDER_ID]}
                media = MediaFileUpload(temp_path, mimetype=file.mimetype, resumable=True)
                uploaded_file = drive_service.files().create(
                    body=file_metadata, media_body=media, fields='id'
                ).execute()

                file_id = uploaded_file.get('id')
                if file_id:
                    drive_service.permissions().create(
                        fileId=file_id, body={'role': 'reader', 'type': 'anyone'}
                    ).execute()
                    file_link = f"https://drive.google.com/file/d/{file_id}/view"
                    uploaded_links.append(f"📄 `{file.filename}` → [View File]({file_link})")

            message_content = (
                f"📥 **New Files Uploaded**\n"
                f"👤 Uploaded by: <@{uploader_id}>\n"
                + '\n'.join(uploaded_links)
            )
            webhook_response = requests.post(UPLOAD_WEBHOOK_URL, json={"content": message_content})
            webhook_success = webhook_response.status_code == 204
            bot_message_sent = send_bot_message(channel_id, message_content)
            
            if not webhook_success or not bot_message_sent:
                return "⚠️ Files uploaded, but failed to send messages to one or more channels."
            
            return "✅ Files uploaded successfully!"
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return "❌ Upload failed. Please try again."
    
    return render_template_string(UPLOAD_FORM, uploader_id=uploader_id, channel_id=channel_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)