

# Voice-Enabled Google Workspace Assistant (Desktop GUI)

**A desktop AI assistant to manage emails and meetings via voice commands, integrating Google Workspace APIs.**

---

## Features

* **Voice Commands**: Speak natural commands like:

  * “Send an email to HR asking for the updated hiring report.”
  * “Schedule a meeting tomorrow at 10 AM with the finance team.”
* **Gmail Integration**: Draft and send emails automatically.
* **Google Calendar Integration**: Schedule meetings with attendees and automatic time parsing.
* **Text-to-Speech Feedback**: Assistant confirms actions vocally.
* **Modern GUI**:

  * Status updates
  * Last command & assistant response display
  * Quick action buttons
* **Intent Recognition via LLM** (Groq): Extracts email/meeting parameters from natural speech.
* Tracks sent emails and scheduled meetings locally.

---

![Interface](relative/path/to/Screenshot.png)

---

## Requirements

Python 3.10+ with the following packages:

```text
tkinter
speechrecognition
pyttsx3
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
groq
dateparser
```

> **Note**: `PyAudio` may require platform-specific installation. On Windows, use precompiled binaries from [PyAudio Windows Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

---

## Setup Instructions

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd <repo-folder>
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Add Google Credentials**

* Go to [Google Cloud Console](https://console.cloud.google.com/).
* Create a project and enable **Gmail API** and **Google Calendar API**.
* Download `credentials.json` and place it in the project root.

4. **Run the Assistant**

```bash
python assistant.py
```

5. **Authorize Google APIs**

* The first run will open a browser for Google authentication.
* A `token.pickle` file will be created for future runs.

---

## How to Use

* Click **Start Listening** and speak commands naturally.
* Use quick action buttons for guidance.
* The assistant will respond in voice and display the response in the GUI.
* Sent emails and scheduled meetings can be viewed using the **Show Items** button.

---

## Notes

* Requires an active internet connection for Google API calls and LLM processing.
* Voice recognition may vary depending on microphone quality and background noise.
* LLM API key must be valid for intent extraction.

---

