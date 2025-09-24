#!/usr/bin/env python3
"""
Voice-enabled Google Workspace Assistant with GUI
Improved version with better error handling and visibility
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import speech_recognition as sr
import pyttsx3
import os
import json
import base64
import pickle
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq
import dateparser

class VoiceGoogleAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Google Workspace Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS engine
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.8)
        
        # Groq LLM configuration
        self.groq_client = Groq(api_key="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")
        self.llm_model = "llama-3.3-70b-versatile"
        
        # Google API configuration
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/calendar'
        ]
        self.GOOGLE_CREDENTIALS_FILE = 'credentials.json'
        
        # Initialize services
        self.gmail_service = None
        self.calendar_service = None
        self.authenticate_google()
        
        # Track created items
        self.sent_emails = []
        self.scheduled_meetings = []
        
        # GUI state variables
        self.is_listening = False
        self.listening_thread = None
        
        self.setup_gui()
        self.update_status("Ready to assist you!")
        
        print("Voice Google Assistant with GUI initialized successfully!")
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Header frame
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="Voice Google Workspace Assistant", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(pady=20)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#f0f0f0')
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(status_frame, text="Status: Ready", font=('Arial', 10), 
                                    bg='#f0f0f0', fg='#2c3e50')
        self.status_label.pack(side=tk.LEFT)
        
        # Voice control frame
        voice_frame = tk.Frame(main_frame, bg='#ecf0f1', relief=tk.RAISED, bd=1)
        voice_frame.pack(fill=tk.X, pady=10)
        
        voice_label = tk.Label(voice_frame, text="Voice Control", font=('Arial', 12, 'bold'), 
                              bg='#ecf0f1', fg='#2c3e50')
        voice_label.pack(pady=10)
        
        # Voice button with microphone icon
        self.voice_button = tk.Button(voice_frame, text="🎤  Start Listening", 
                                     font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                                     command=self.toggle_listening, width=20, height=2)
        self.voice_button.pack(pady=10)
        
        # Command display
        command_frame = tk.Frame(main_frame, bg='#f0f0f0')
        command_frame.pack(fill=tk.X, pady=5)
        
        cmd_label = tk.Label(command_frame, text="Last Command:", font=('Arial', 10, 'bold'), 
                            bg='#f0f0f0', fg='#2c3e50')
        cmd_label.pack(anchor=tk.W)
        
        self.command_text = scrolledtext.ScrolledText(command_frame, height=3, 
                                                     font=('Arial', 10), wrap=tk.WORD)
        self.command_text.pack(fill=tk.X, pady=5)
        self.command_text.config(state=tk.DISABLED)
        
        # Response display
        response_frame = tk.Frame(main_frame, bg='#f0f0f0')
        response_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        resp_label = tk.Label(response_frame, text="Assistant Response:", 
                             font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        resp_label.pack(anchor=tk.W)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=8, 
                                                      font=('Arial', 10), wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.response_text.config(state=tk.DISABLED)
        
        # Quick actions frame
        actions_frame = tk.Frame(main_frame, bg='#f0f0f0')
        actions_frame.pack(fill=tk.X, pady=10)
        
        actions_label = tk.Label(actions_frame, text="Quick Actions", 
                                font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        actions_label.pack()
        
        buttons_frame = tk.Frame(actions_frame, bg='#f0f0f0')
        buttons_frame.pack(pady=10)
        
        # Quick action buttons
        email_btn = tk.Button(buttons_frame, text="Send Email", bg='#e74c3c', fg='white',
                             command=lambda: self.quick_action("send_email"))
        email_btn.pack(side=tk.LEFT, padx=5)
        
        meeting_btn = tk.Button(buttons_frame, text="Schedule Meeting", bg='#27ae60', fg='white',
                               command=lambda: self.quick_action("schedule_meeting"))
        meeting_btn.pack(side=tk.LEFT, padx=5)
        
        show_btn = tk.Button(buttons_frame, text="Show Items", bg='#f39c12', fg='white',
                            command=lambda: self.quick_action("show_items"))
        show_btn.pack(side=tk.LEFT, padx=5)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#2c3e50', height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(footer_frame, text="Voice Google Workspace Assistant v2.0", 
                               font=('Arial', 8), fg='white', bg='#2c3e50')
        footer_label.pack(pady=5)
    
    def update_status(self, message):
        """Update the status label"""
        self.status_label.config(text=f"Status: {message}")
        self.root.update_idletasks()
    
    def update_command_display(self, text):
        """Update the command display area"""
        self.command_text.config(state=tk.NORMAL)
        self.command_text.delete(1.0, tk.END)
        self.command_text.insert(tk.END, text)
        self.command_text.config(state=tk.DISABLED)
    
    def update_response_display(self, text):
        """Update the response display area"""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, text)
        self.response_text.config(state=tk.DISABLED)
    
    def toggle_listening(self):
        """Toggle listening state"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Start listening for voice commands"""
        self.is_listening = True
        self.voice_button.config(text="🔴 Stop Listening", bg='#e74c3c')
        self.update_status("Listening... Speak now!")
        
        # Start listening in a separate thread to avoid blocking the GUI
        self.listening_thread = threading.Thread(target=self.listen_and_process)
        self.listening_thread.daemon = True
        self.listening_thread.start()
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.is_listening = False
        self.voice_button.config(text="🎤 Start Listening", bg='#3498db')
        self.update_status("Ready")
    
    def listen_and_process(self):
        """Listen for voice commands and process them"""
        try:
            command = self.listen_to_speech(timeout=15)
            self.root.after(0, self.process_command, command)
        except Exception as e:
            self.root.after(0, self.update_status, f"Error: {str(e)}")
    
    def listen_to_speech(self, timeout=15):
        """Capture voice input with better timeout handling"""
        try:
            print("\n🎤 Listening... Speak now!")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=20)
            
            text = self.recognizer.recognize_google(audio)
            print(f"🗣️ You said: {text}")
            return text.lower()
        
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "unknown"
        except Exception as e:
            print(f"❌ Speech recognition error: {e}")
            return "error"
    
    def speak_text(self, text):
        """Convert text to speech"""
        print(f"🤖 Assistant: {text}")
        self.update_response_display(text)
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def authenticate_google(self):
        """Authenticate with Google APIs"""
        creds = None
        token_file = 'token.pickle'
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(f"Google credentials file '{self.GOOGLE_CREDENTIALS_FILE}' not found")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.GOOGLE_CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        self.calendar_service = build('calendar', 'v3', credentials=creds)
        print("Google APIs authenticated successfully!")
    
    def extract_parameters_with_llm(self, user_input):
        """Use Groq LLM to understand intent and extract parameters"""
        
        system_prompt = """You are a helpful AI assistant that manages emails and calendar events. 
        Analyze the user's command and extract parameters for email or meeting creation.

        Return a JSON object with:
        - intent: "send_email", "schedule_meeting", "show_items", "unknown"
        - parameters: object with extracted details
        - needs_clarification: boolean
        - clarification_question: string if clarification needed

        For emails, extract:
        - to_email: recipient email address
        - subject: email subject
        - body: email content

        For meetings, extract:
        - title: meeting title
        - start_time: in natural language
        - duration: meeting duration (default to 1 hour if not specified)
        - attendees: list of email addresses
        - description: meeting description

        For showing items (when user says "show my emails", "what meetings do I have", etc.):
        - items_to_show: "emails", "meetings", or "both"

        Use natural language processing for times. If email domain is not specified, use @company.com as default.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"❌ LLM processing error: {e}")
            return self.fallback_intent_detection(user_input)
    
    def fallback_intent_detection(self, user_input):
        """Improved fallback intent detection"""
        user_input_lower = user_input.lower()
        
        # Check for show commands first
        if any(word in user_input_lower for word in ['show', 'list', 'what', 'view', 'see']):
            if any(word in user_input_lower for word in ['email', 'mail']):
                return {
                    "intent": "show_items",
                    "parameters": {"items_to_show": "emails"},
                    "needs_clarification": False
                }
            elif any(word in user_input_lower for word in ['meeting', 'event', 'calendar']):
                return {
                    "intent": "show_items",
                    "parameters": {"items_to_show": "meetings"},
                    "needs_clarification": False
                }
            else:
                return {
                    "intent": "show_items",
                    "parameters": {"items_to_show": "both"},
                    "needs_clarification": False
                }
        
        elif any(word in user_input_lower for word in ['email', 'send', 'mail']):
            return {
                "intent": "send_email",
                "parameters": {},
                "needs_clarification": True,
                "clarification_question": "I understand you want to send an email. Please tell me the recipient, subject, and message content."
            }
        elif any(word in user_input_lower for word in ['meeting', 'schedule', 'calendar', 'appointment']):
            return {
                "intent": "schedule_meeting",
                "parameters": {},
                "needs_clarification": True,
                "clarification_question": "I understand you want to schedule a meeting. Please tell me the time, title, and any attendees."
            }
        else:
            return {
                "intent": "unknown",
                "parameters": {},
                "needs_clarification": False
            }
    
    def send_email_action(self, parameters):
        """Send email using Gmail API"""
        try:
            to_email = parameters.get('to_email', '')
            subject = parameters.get('subject', 'No subject')
            body = parameters.get('body', '')
            
            if not to_email or '@' not in to_email:
                return False, "Valid recipient email address is required"
            
            # Create email message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message_body = {'raw': encoded_message}
            
            message = self.gmail_service.users().messages().send(
                userId='me', body=message_body).execute()
            
            # Track sent email
            email_info = {
                'to': to_email,
                'subject': subject,
                'body': body,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.sent_emails.append(email_info)
            
            return True, f"Email sent successfully to {to_email}"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def schedule_meeting_action(self, parameters):
        """Schedule meeting using Google Calendar API"""
        try:
            title = parameters.get('title', 'Meeting')
            start_time_str = parameters.get('start_time', '')
            duration = parameters.get('duration', '1 hour')
            attendees = parameters.get('attendees', [])
            description = parameters.get('description', '')
            
            if not start_time_str:
                return False, "Meeting time is required"
            
            # Parse start time
            start_time = dateparser.parse(start_time_str)
            if not start_time:
                return False, f"Could not understand the meeting time: {start_time_str}"
            
            # Calculate end time based on duration
            if 'hour' in duration.lower():
                hours = int(''.join(filter(str.isdigit, duration)) or 1)
                end_time = start_time + timedelta(hours=hours)
            elif 'minute' in duration.lower():
                minutes = int(''.join(filter(str.isdigit, duration)) or 30)
                end_time = start_time + timedelta(minutes=minutes)
            else:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
            }
            
            # Add attendees if provided
            if attendees and isinstance(attendees, list):
                valid_attendees = [email.strip() for email in attendees if '@' in email]
                if valid_attendees:
                    event['attendees'] = [{'email': email} for email in valid_attendees]
            
            event = self.calendar_service.events().insert(
                calendarId='primary', body=event).execute()
            
            # Track scheduled meeting
            meeting_info = {
                'title': title,
                'start_time': start_time.strftime("%Y-%m-%d %H:%M"),
                'duration': duration,
                'attendees': attendees,
                'description': description
            }
            self.scheduled_meetings.append(meeting_info)
            
            meeting_time = start_time.strftime('%A, %B %d at %I:%M %p')
            return True, f"Meeting '{title}' scheduled for {meeting_time}"
            
        except Exception as e:
            return False, f"Failed to schedule meeting: {str(e)}"
    
    def show_items_action(self, parameters):
        """Show saved emails and meetings"""
        items_to_show = parameters.get('items_to_show', 'both')
        response = ""
        
        if items_to_show in ['emails', 'both']:
            if self.sent_emails:
                response += f" You've sent {len(self.sent_emails)} emails:\n"
                for i, email in enumerate(self.sent_emails[-5:], 1):  # Show last 5
                    response += f"{i}. To: {email['to']} - {email['subject']}\n"
            else:
                response += "No emails sent yet.\n"
        
        if items_to_show in ['meetings', 'both']:
            if self.scheduled_meetings:
                response += f"You've scheduled {len(self.scheduled_meetings)} meetings:\n"
                for i, meeting in enumerate(self.scheduled_meetings[-5:], 1):  # Show last 5
                    response += f"{i}. {meeting['title']} at {meeting['start_time']}\n"
            else:
                response += "No meetings scheduled yet.\n"
        
        return True, response if response else "No items to show."
    
    def execute_action(self, intent, parameters):
        """Execute the appropriate action based on intent"""
        if intent == "send_email":
            return self.send_email_action(parameters)
        elif intent == "schedule_meeting":
            return self.schedule_meeting_action(parameters)
        elif intent == "show_items":
            return self.show_items_action(parameters)
        else:
            return False, "I can help you send emails, schedule meetings, or show your recent items."
    
    def process_command(self, command):
        """Process voice commands"""
        if command in ["timeout", "unknown", "error"]:
            if command == "timeout":
                self.speak_text("I didn't hear anything. Please try again when you're ready.")
            elif command == "unknown":
                self.speak_text("I couldn't understand what you said. Please try again.")
            self.stop_listening()
            return
        
        self.update_command_display(command)
        self.update_status("Processing your command...")
        
        # Process with LLM
        llm_result = self.extract_parameters_with_llm(command)
        
        intent = llm_result.get('intent', 'unknown')
        parameters = llm_result.get('parameters', {})
        
        # Execute action
        if intent != 'unknown':
            success, message = self.execute_action(intent, parameters)
            self.speak_text(message)
        else:
            self.speak_text("I can help you send emails, schedule meetings, or show your recent items. What would you like to do?")
        
        self.stop_listening()
    
    def quick_action(self, action_type):
        """Handle quick action buttons"""
        if action_type == "send_email":
            self.speak_text("Please use voice command to send an email. Say something like 'Send an email to John about the project update'.")
        elif action_type == "schedule_meeting":
            self.speak_text("Please use voice command to schedule a meeting. Say something like 'Schedule a meeting with the team tomorrow at 2 PM'.")
        elif action_type == "show_items":
            success, message = self.show_items_action({"items_to_show": "both"})
            self.speak_text(message)

def main():
    """Main function to run the assistant"""
    print("Starting Voice Google Workspace Assistant with GUI...")
    print("Features:")
    print("  • Modern GUI with intuitive controls")
    print("  • Real-time status updates")
    print("  • Command and response display")
    print("  • Quick action buttons")
    print("  • Threaded voice processing")
    
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json file not found")
        print("Please download Google API credentials from Google Cloud Console")
        return
    
    try:
        root = tk.Tk()
        app = VoiceGoogleAssistantGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")

if __name__ == "__main__":
    main()