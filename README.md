
# Multi-File Uploader with Discord Bot Integration

This project provides a **Flask web application** for file uploads and a **Discord bot** that integrates with the Flask app to manage file uploads, role management, and ticketing systems within Discord.

## Features

### Flask App:
- Allows users to upload files to **Google Drive**.
- Provides a **shareable link** for each uploaded file.
- Sends file upload notifications to a **Discord channel**.

### Discord Bot:
- **File Upload Notifications**: Notifies users when a file is uploaded.
- **Ticketing System**: Creates support tickets when users click the button in Discord.
- **Role Management**: Users can request roles via reactions to messages.

---

## Installation

### 1. Set Up the Flask App

#### Requirements:
- Python 3.7 or higher
- Install required packages:

```bash
pip install flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
```

#### Set Up Google Drive API:
1. Go to the [Google Cloud Console](https://console.developers.google.com/).
2. Create a project and enable the **Google Drive API**.
3. Create a **service account** and download the **credentials JSON** file.
4. Rename the downloaded file as `googlecredentialsfile.json` and place it in your project directory.

#### Set Up Environment Variables:
Create a `.env` file in your project root directory and set the following environment variables:

```bash
GOOGLE_CREDENTIALS_FILE=googlecredentialsfile.json
GOOGLE_DRIVE_FOLDER_ID=your-google-drive-folder-id
DISCORD_UPLOAD_WEBHOOK_URL=your-discord-webhook-url
DISCORD_BOT_TOKEN=your-discord-bot-token
```

#### Running the Flask App:
To run the Flask app, use the following command:

```bash
python app.py
```

The app will be accessible at `http://localhost:5000` in your browser. This is where users can upload files.

---

### 2. Set Up the Discord Bot

#### Requirements:
- Python 3.7 or higher
- Install required packages:

```bash
pip install discord.py
```

#### Set Up Discord Bot:
1. Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
2. Generate the bot token and invite the bot to your server with the following permissions:
    - `Send Messages`
    - `Manage Roles`
    - `Read Message History`
3. Set the following environment variables for the bot:

```bash
DISCORD_BOT_TOKEN=your-discord-bot-token
UPLOAD_FORM_URL=http://yourappurl.com  # URL of your Flask app
UPLOAD_CHANNEL_NAME=upload  # Channel for webhook notifications
```

#### Running the Bot:
To run the Discord bot, execute the following command:

```bash
python discord_bot.py
```

The bot will now be active and ready to interact with users in Discord.

---

### 3. Additional Features:

#### File Upload Feature:
- The Flask app provides a file upload form. Users can upload files to **Google Drive**.
- After uploading, a **shareable link** for the uploaded file is sent to the Discord channel.

#### Ticketing System:
- Users can create a support ticket by using the `!ticket` command in Discord. 
- A private ticketing channel is created, where users can interact with the support team.

#### Role Management:
- Users can request roles by reacting to a message in Discord with specific emojis.
- Admins can approve or deny role requests through a simple button interface.

---

## Project Structure:

```
/project-root
│
├── app.py                 # Flask app for handling file uploads
├── discord_bot.py         # Discord bot handling notifications and commands
├── .env                   # Environment variables (Google API credentials, Bot Token)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---


## Support

For any issues or suggestions, feel free to open an issue on the repository or contact me directly.

---

Made with ❤️ by Hasnain
