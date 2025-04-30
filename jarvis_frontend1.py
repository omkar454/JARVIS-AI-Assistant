import customtkinter as ctk
from tkinter import filedialog
import threading
import sys
import time
import speech_recognition as sr
from datetime import datetime
import psutil
import os
import queue
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import webbrowser
import instaloader
import code_segment
import pyttsx3
import tkinter as tk
from MainJarvis_TaskExecution import send_to_Gemini


# Backend Imports
from MainJarvis_TaskExecution import (
     hide_folder, unhide_folder, copy_file, copy_folder, speak,
    move_file, move_folder, delete_file, delete_folder, archieve_zip,
    extract_zip, create_file, create_folder, execute_system_command, greet
)

# Initialize Text-to-Speech Engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speaker(audio):
    """Speaks the provided audio string."""
    engine.say(audio)
    engine.runAndWait()

def takeCommand():
    """Takes voice input from the user and returns it as text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=15, phrase_time_limit=30)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            speak("I did not catch that, Sir. Please say it again.")
            return takeCommand()
        except sr.RequestError:
            speak("I am unable to connect to the speech recognition service. Please check your internet connection.")
            return "error"
        except sr.WaitTimeoutError:
            speak("You did not say anything. Please say something, Sir.")
            return "error"
        except OSError:
            speak("Sir, I cannot access the microphone. Please check if it is connected.")
            return "error"
        except Exception as e:
            speak("Sorry Sir. Unable to recognize your voice. Please say it again.")
            print(f"Error: {e}")
            return "error"

def generate_email_content_with_gemini(email_context: str, tone: str = "formal", recipient_type: str = "general"):
    """
    Generates a realistic, human-like email with a subject and body, based on the context, tone, and recipient type.

    Args:
        email_context (str): The situation or content of the email.
        tone (str): 'formal' or 'informal'. Default is 'formal'.
        recipient_type (str): The kind of person receiving the email (e.g., 'friend', 'boss', 'parent').

    Returns:
        tuple: (subject, body) of the generated email. If error occurs, returns (None, error_message).
    """

    prompt = f"""
You are a helpful assistant skilled at writing realistic, human-like emails.

Write an email using the following details:

Context: "{email_context}"
Tone: "{tone}"
Recipient Type: "{recipient_type}"

Instructions:
- Generate a short, meaningful subject line.
- Write the email as if a thoughtful person is sending it to a {recipient_type}.
- If the tone is 'formal', use respectful, professional language.
- If the tone is 'informal', be warm, friendly, and natural.
- Adapt the language to suit the recipient (e.g., friendly for a friend, respectful for a teacher).
- DO NOT mention you're an AI or reference model limitations.
- DO NOT include "(Your Name Here)" — use natural language like "I", or "Omkar" if fitting.

Format:
Subject: <your subject line>

Body:
<your email body>
"""

    try:
        # from MainJarvis_TaskExecution import send_to_Gemini
        response = send_to_Gemini(prompt)

        # Make sure response is a string
        if not isinstance(response, str):
            return None, "Gemini response is not a string."

        subject = "No Subject Generated"
        body = "No message content available."

        if "Subject:" in response and "Body:" in response:
            parts = response.split("Body:")
            subject_line = parts[0].replace("Subject:", "").strip()
            body_text = parts[1].strip()
            subject = subject_line
            body = body_text
        else:
            # fallback if Gemini replies only with body text
            subject = "No Subject Found"
            body = response.strip()

        return subject, body

    except Exception as e:
        return None, f"Error generating email content using Gemini: {str(e)}"




class RedirectText:
    """Redirects standard output to the chat display."""
    def __init__(self, app):
        self.app = app
        self.queue = queue.Queue()

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass  # Needed for compatibility

    def update_display(self):
        while not self.queue.empty():
            text = self.queue.get().strip()
            if text:
                self.app.display_message(text, sender="JARVIS")  # Show as a JARVIS message




class JarvisChatApp(ctk.CTk):
    def __init__(self):

        super().__init__()

        # Theme Colors and Fonts
        self.BG_COLOR = "#000000"
        self.FRAME_BG_COLOR = "#1E1E1E"
        self.SIDEBAR_BG_COLOR = "#181818"
        self.TEXT_COLOR = "#E0E0E0"
        self.ACCENT_COLOR = "#00BFFF"
        self.USER_MSG_COLOR = "#00FFFF"
        self.BUTTON_COLOR = "#2A2A2A"
        self.BUTTON_HOVER_COLOR = "#383838"
        self.ENTRY_BG_COLOR = "#252525"
        self.ENTRY_BORDER_COLOR = "#333333"
        self.USER_BUBBLE_COLOR = "#404040"
        self.JARVIS_BUBBLE_COLOR = "#282828"
        self.TRANSPARENT_COLOR = "#00000000"

        self.TITLE_FONT = ctk.CTkFont("Consolas", 26, "bold")
        self.LABEL_FONT = ctk.CTkFont("Segoe UI Variable Text", 14, "bold")
        self.BUTTON_FONT = ctk.CTkFont("Segoe UI Variable Text", 12)
        self.TEXT_FONT = ctk.CTkFont("Segoe UI Variable Text", 14)
        self.ENTRY_FONT = ctk.CTkFont("Segoe UI Variable Text", 15)
        self.ICON_FONT = ctk.CTkFont("Segoe UI Symbol", 16)

        self.window = self
        self.title("JARVIS Interface")
        self.geometry("950x650")
        self.configure(bg=self.BG_COLOR)
        ctk.set_appearance_mode("dark")

        

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(self, text="J.A.R.V.I.S.", font=self.TITLE_FONT, text_color=self.ACCENT_COLOR).grid(row=0, column=0, columnspan=2, pady=(15, 10))

        # Clock & Date
        self.clock_label = ctk.CTkLabel(self, text="", text_color=self.USER_MSG_COLOR, font=self.BUTTON_FONT)
        self.clock_label.place(x=10, y=10)
        self.date_label = ctk.CTkLabel(self, text="", text_color=self.USER_MSG_COLOR, font=self.BUTTON_FONT)
        self.date_label.place(relx=1.0, y=10, anchor="ne", x=-10)
        self.update_time_date()

        # Separator
        self.separator_top = ctk.CTkFrame(self, height=1, fg_color=self.ACCENT_COLOR, bg_color="#1A1A1A")
        self.separator_top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(50, 5))

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, fg_color=self.SIDEBAR_BG_COLOR, width=230, corner_radius=10)
        self.sidebar_frame.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="ns")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="Chat History", text_color=self.ACCENT_COLOR, font=self.LABEL_FONT).grid(row=0, column=0, padx=10, pady=(15, 10))

        self.history_listbox = ctk.CTkTextbox(self.sidebar_frame, fg_color=self.FRAME_BG_COLOR, text_color=self.TEXT_COLOR, font=self.TEXT_FONT,
                                              border_width=1, border_color=self.ENTRY_BORDER_COLOR, corner_radius=5, state="disabled", wrap="word",
                                              scrollbar_button_color="#222222", scrollbar_button_hover_color=self.ACCENT_COLOR)
        self.history_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        ctk.CTkButton(self.sidebar_frame, text="Clear History", command=self.clear_history,
                      fg_color=self.BUTTON_COLOR, hover_color=self.BUTTON_HOVER_COLOR, text_color=self.TEXT_COLOR,
                      font=self.BUTTON_FONT, corner_radius=5).grid(row=2, column=0, padx=10, pady=(5, 15))

        # Chat Frame
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(1, weight=1)

        self.chat_display = ctk.CTkScrollableFrame(self.chat_frame, fg_color="transparent",
                                                   scrollbar_button_color="#222222", scrollbar_button_hover_color=self.ACCENT_COLOR)
        self.chat_display.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.chat_display.grid_columnconfigure(0, weight=1)

        self.separator_bottom = ctk.CTkFrame(self.chat_frame, height=1, fg_color=self.ACCENT_COLOR, bg_color="#1A1A1A")
        self.separator_bottom.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 5))

        # Input Frame
        self.bottom_input_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.bottom_input_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="ew")
        self.bottom_input_frame.grid_columnconfigure(2, weight=1)

        self.file_button = ctk.CTkButton(self.bottom_input_frame, text="📂", fg_color=self.BUTTON_COLOR,
                                         hover_color=self.BUTTON_HOVER_COLOR, text_color=self.ACCENT_COLOR, font=self.ICON_FONT,
                                         command=self.open_file_dialog, width=35, corner_radius=5)
        self.file_button.grid(row=0, column=0, padx=(0, 5), pady=5)

        self.mic_button = ctk.CTkButton(self.bottom_input_frame, text="🎤", fg_color=self.BUTTON_COLOR,
                                        hover_color=self.ACCENT_COLOR, text_color=self.ACCENT_COLOR, font=self.ICON_FONT,
                                        command=self.start_voice_input, width=35, corner_radius=5)
        self.mic_button.grid(row=0, column=1, padx=(0, 5), pady=5)

        self.animate_mic_button()

        self.input_box = ctk.CTkEntry(self.bottom_input_frame, placeholder_text="Type your message or command...",
                                      fg_color=self.ENTRY_BG_COLOR, text_color=self.TEXT_COLOR,
                                      border_color=self.ENTRY_BORDER_COLOR, font=self.ENTRY_FONT,
                                      border_width=1, corner_radius=5)
        self.input_box.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="ew")
        self.input_box.bind("<Return>", lambda event: self.process_input())

        self.send_button = ctk.CTkButton(self.bottom_input_frame, text="➤", fg_color=self.BUTTON_COLOR,
                                         hover_color=self.BUTTON_HOVER_COLOR, text_color=self.ACCENT_COLOR,
                                         font=self.ICON_FONT, command=self.process_input, width=35, corner_radius=5)
        self.send_button.grid(row=0, column=3, padx=(0, 0), pady=5)

        # System Info Frame
        self.system_info_frame = ctk.CTkFrame(self.chat_frame, fg_color=self.BG_COLOR, corner_radius=10)
        self.system_info_frame.grid(row=3, column=0, padx=(5, 2), pady=(5, 0), sticky="ew")
        self.system_info_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.system_info_frame, text="System Info", text_color=self.ACCENT_COLOR, font=self.LABEL_FONT).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.battery_label = ctk.CTkLabel(self.system_info_frame, text="Battery: --%", text_color=self.TEXT_COLOR, font=self.BUTTON_FONT)
        self.battery_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        self.cpu_label = ctk.CTkLabel(self.system_info_frame, text="CPU: --%", text_color=self.TEXT_COLOR, font=self.BUTTON_FONT)
        self.cpu_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        self.ram_label = ctk.CTkLabel(self.system_info_frame, text="RAM: --%", text_color=self.TEXT_COLOR, font=self.BUTTON_FONT)
        self.ram_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")

        self.disk_label = ctk.CTkLabel(self.system_info_frame, text="Disk: --%", text_color=self.TEXT_COLOR, font=self.BUTTON_FONT)
        self.disk_label.grid(row=4, column=0, padx=10, pady=(2, 10), sticky="w")

        self.update_system_info()

                # Bottom Right Boot Log Panel (within chat_frame)
        self.boot_log_frame = ctk.CTkFrame(self.chat_frame, fg_color=self.BG_COLOR, corner_radius=10)
        self.boot_log_frame.grid(row=3, column=1, padx=(2, 5), pady=(5, 0), sticky="nsew")
        self.boot_log_frame.grid_columnconfigure(0, weight=1)
        self.boot_log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.boot_log_frame, text="Boot Log", text_color=self.ACCENT_COLOR, font=self.LABEL_FONT).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="ew"
        )

        self.boot_log_textbox = ctk.CTkTextbox(
            self.boot_log_frame,
            fg_color=self.BG_COLOR,
            text_color=self.TEXT_COLOR,
            font=self.TEXT_FONT,
            border_width=0,
            wrap="word",
            height=100,
            scrollbar_button_color="#222222",
            scrollbar_button_hover_color=self.ACCENT_COLOR
        )
        self.boot_log_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.boot_log_textbox.configure(state="disabled")
        self.load_boot_log()

        # Redirect stdout to chat display
        self.typing_label = None
        self.redirector = RedirectText(self.chat_display)
        sys.stdout = self.redirector
        self.after(100, self.update_gui)


        # Multi-step input tracking
        self.pending_command = None  # Store the original command
        self.pending_responses = []  # Store user responses
        self.expected_responses = 0  # Number of expected user responses

        # Regular GUI update
        self.window.after(100, self.update_gui)

        # Email command state
        self.email_state = None
        self.email_data = {}

        # Instagram state
        self.insta_state = None
        self.insta_username = ""

        # Crypto storage
        self.stored_crypto_name = None

        # Redirect stdout/stderr to CTkTextbox
        self.redirector = RedirectText(self)
        sys.stdout = self.redirector
        sys.stderr = self.redirector
        self.update_gui()
 # start the loop to refresh every 100ms



        # Initial greeting trigger
        self.after(500, self.initial_greet)



    def process_input(self, event=None):
        from tkinter import END
        user_input = self.input_box.get().strip()
        if not user_input:
            return

        self.input_box.delete(0, END)
        self.display_message(f"{user_input}\n", sender="You", user=True)
        self.history_listbox.insert(END, user_input)

        # PRIORITIZE Instagram Handling
        if self.insta_state:
            self.handle_insta_input(user_input)
            return

        # PRIORITIZE Email Handling
        if self.email_state:
            self.handle_email_input(user_input)
            return

        # Copy File Handling
        if "copy file" in user_input.lower():
            self.pending_command = "copy_file"
            self.expected_responses = 2
            speak("Sir, please enter the source file path along with its extension.")
            # self.display_message("Enter the source file path with extension:", "JARVIS", False)
            return

        if self.pending_command == "copy_file":
            if not hasattr(self, 'source_path'):
                self.source_path = user_input.strip()
                speak("Sir, please enter the destination file path.")
                # self.display_message("Enter the destination file path:", "JARVIS", False)
            else:
                destination_path = user_input.strip()
                copy_file(self.source_path, destination_path)
                # self.display_message("✅ File copied successfully.", "JARVIS", False)
                # speak("Sir, the file has been copied successfully.")

                del self.source_path
                self.pending_command = None
            return

        # Copy Folder Handling
        if "copy folder" in user_input.lower() or "copy directory" in user_input.lower():
            self.pending_command = "copy_folder"
            self.expected_responses = 2
            speak("Sir, please enter the source folder path.")
            # self.display_message("Enter the source folder path:", "JARVIS", False)
            return

        if self.pending_command == "copy_folder":
            if not hasattr(self, 'source_folder'):
                self.source_folder = user_input.strip()
                speak("Sir, please enter the destination folder path (must not exist).")
                # self.display_message("Enter the destination folder path:", "JARVIS", False)
            else:
                destination_folder = user_input.strip()
                copy_folder(self.source_folder, destination_folder)
                # self.display_message("✅ Folder copied successfully.", "JARVIS", False)
                # speak("Sir, the folder has been copied successfully.")

                del self.source_folder
                self.pending_command = None
            return

        # Move File Handling
        if "move file" in user_input.lower():
            self.pending_command = "move_file"
            self.expected_responses = 2
            speak("Sir, please enter the source file path along with its extension.")
            # self.display_message("Enter the source file path with extension:", "JARVIS", False)
            return

        if self.pending_command == "move_file":
            if not hasattr(self, 'source_path'):
                self.source_path = user_input.strip()
                speak("Sir, please enter the destination file path.")
                # self.display_message("Enter the destination file path:", "JARVIS", False)
            else:
                destination_path = user_input.strip()
                move_file(self.source_path, destination_path)
                # self.display_message("✅ File moved successfully.", "JARVIS", False)
                # speak("Sir, the file has been moved successfully.")

                del self.source_path
                self.pending_command = None
                
                        # **Move Folder Handling**
        elif "move folder" in user_input.lower() or "move directory" in user_input.lower():
            self.pending_command = "move_folder"
            self.expected_responses = 2  # Expecting source and destination paths
            speak("Sir, please enter the source folder path.")
            # self.display_message("Enter the source folder path:", "JARVIS", False)

        elif self.pending_command == "move_folder":
            if not hasattr(self, 'source_folder'):
                self.source_folder = user_input.strip()
                speak("Sir, please enter the destination folder path.")
                # self.display_message("Enter the destination folder path:", "JARVIS", False)
            else:
                destination_folder = user_input.strip()
                move_folder(self.source_folder, destination_folder)  # Call the backend function
                # self.display_message("✅ Folder moved successfully.", "JARVIS", False)
                # speak("Sir, the folder has been moved successfully.")

                del self.source_folder  # Remove stored path
                self.pending_command = None  # Reset state

        # Unhide Folder
        elif self.pending_command == "unhide_folder":
            # user_input = input()
            result = unhide_folder(user_input)  # Pass the folder path
            # if result:  # Ensure it's not None
            #     self.display_message(result, "JARVIS", False)
            self.pending_command = None  # Reset state

        # Hide Folder
        elif self.pending_command == "hide_folder":
            # user_input = input()
            result = hide_folder(user_input)  # Pass the folder path
            # if result:  # Ensure it's not None
            #     self.display_message(result, "JARVIS", False)
            self.pending_command = None  # Reset state

        elif "delete file" in user_input:
            speak("Sir, please enter the file path along with its extension.")
            # self.display_message("Enter the file path with extension:", "JARVIS", False)
            self.pending_command = "delete_file"

        elif self.pending_command == "delete_file":
            file_path = user_input.strip()
            delete_file(file_path)
            # self.display_message("✅ File deleted successfully.", "JARVIS", False)
            self.pending_command = None  # Reset state

        elif "delete folder" in user_input or "delete directory" in user_input:
            speak("Sir, please enter the folder path.")
            # self.display_message("Enter the folder path:", "JARVIS", False)
            self.pending_command = "delete_folder"

        elif self.pending_command == "delete_folder":
            folder_path = user_input.strip()
            delete_folder(folder_path)
            # self.display_message("✅ Folder deleted successfully.", "JARVIS", False)
            self.pending_command = None  # Reset state

        elif "archive zip" in user_input.lower() or "compress folder" in user_input.lower():
            speak("Sir, please enter the source folder path to archive.")
            # self.display_message("Enter the source folder path to archive:", "JARVIS", False)
            self.pending_command = "archive_zip"
            self.expected_responses = 3  # Expecting source, destination, and zip name

        elif self.pending_command == "archive_zip":
            if not hasattr(self, 'zip_source'):
                self.zip_source = user_input.strip()
                speak("Sir, please enter the destination folder where you want to save the ZIP file.")
                # self.display_message("Enter the destination folder path:", "JARVIS", False)
            elif not hasattr(self, 'zip_destination'):
                self.zip_destination = user_input.strip()
                speak("Sir, please enter the name of the ZIP file (without .zip extension).")
                # self.display_message("Enter the ZIP file name:", "JARVIS", False)
            else:
                zip_name = user_input.strip()
                archieve_zip(self.zip_source, self.zip_destination, zip_name)  
                # self.display_message(f"✅ Folder archived successfully as {zip_name}.zip.", "JARVIS", False)

                del self.zip_source  
                del self.zip_destination  
                self.pending_command = None  

        elif "extract zip" in user_input.lower():
            speak("Sir, please enter the ZIP file path along with .zip extension.")
            # self.display_message("Enter the ZIP file path:", "JARVIS", False)
            self.pending_command = "extract_zip"
            self.expected_responses = 2  # Expecting ZIP file path and destination

        elif self.pending_command == "extract_zip":
            if not hasattr(self, 'zip_file'):
                self.zip_file = user_input.strip()
                speak("Sir, please enter the destination folder where you want to extract the ZIP file.")
                # self.display_message("Enter the destination folder:", "JARVIS", False)
            else:
                destination_folder = user_input.strip()
                extract_zip(self.zip_file, destination_folder)  
                # self.display_message("✅ ZIP extracted successfully.", "JARVIS", False)

                del self.zip_file  
                self.pending_command = None 

        elif "create folder" in user_input.lower() or "new directory" in user_input.lower():
            speak("Sir, please enter the folder path where you want to create the new directory along with its name.")
            # self.display_message("Enter the folder path:", "JARVIS", False)
            self.pending_command = "create_folder"
            self.expected_responses = 1  # Expecting only the folder path

        elif self.pending_command == "create_folder":
            folder_path = user_input.strip()
            create_folder(folder_path)  
            # self.display_message("✅ Folder created successfully.", "JARVIS", False)
            self.pending_command = None  # Reset state

        elif "create file" in user_input.lower() or "new file" in user_input.lower():
            speak("Sir, please enter the full file path including the filename and extension.")
            # self.display_message("Enter the full file path with extension:", "JARVIS", False)
            self.pending_command = "create_file"
            self.expected_responses = 1  # Expecting only the file path

        elif self.pending_command == "create_file":
            file_path = user_input.strip()
            create_file(file_path)  
            # self.display_message("✅ File created successfully.", "JARVIS", False)
            self.pending_command = None  # Reset

        elif self.pending_command == "execute_system_command":
                command = user_input.strip()

                if "rmdir /s" in command:
                    parts = command.split("rmdir /s", 1)
                    if len(parts) > 1:
                        folder_path = parts[1].strip()
                        if not (folder_path.startswith('"') and folder_path.endswith('"')):
                            folder_path = f'"{folder_path}"'  # Auto-fix quotes
                        command = f"rmdir /q /s {folder_path}"  # Ensure /q included

                    speak("Sir, are you sure you want to delete this folder? Type 'Y' to confirm or 'N' to cancel.")
                    self.display_message("⚠️ WARNING: Type 'Y' to confirm deletion or 'N' to cancel:", "JARVIS", False)
                    self.pending_command = "confirm_rmdir"
                    self.stored_command = command
                else:
                    result = execute_system_command(command)
                    self.display_message(result, "JARVIS", False)
                    self.pending_command = None

        elif self.pending_command == "confirm_rmdir":
                confirmation = user_input.strip().lower()
                if confirmation == "y":
                    result = execute_system_command(self.stored_command)
                    self.display_message(result, "JARVIS", False)
                    del self.stored_command
                else:
                    speak("Command discarded. Folder was NOT deleted.")
                    self.display_message("❌ Command discarded. Folder was NOT deleted.", "JARVIS", False)
                self.pending_command = None

        # elif "analyze medical image" in user_input.lower() or "check health" in user_input.lower() or "medical" in user_input.lower():
        #     speak("Sir, please provide the image path for medical analysis.")
        #     # self.display_message("🩺 Enter the image path for medical analysis:", "JARVIS", False)
        #     self.pending_command = "medical_analysis"


        # elif "image" in user_input.lower() or "picture" in user_input.lower() or "photo" in user_input.lower():
        #         speak("Sir, please enter the full file path of the image along with its extension.")
        #         # self.display_message("Enter the full file path of the image:", "JARVIS", False)
        #         self.pending_command = "image_analysis"

        elif self.pending_command == "image_analysis":
                if not hasattr(self, 'image_path'):
                    self.image_path = user_input.strip().strip('"')

                    if not os.path.exists(self.image_path):
                        speak("Sorry Sir. The specified image file does not exist. Please provide a valid path.")
                        # self.display_message("❌ The specified image file does not exist. Please provide a valid path.", "JARVIS", False)
                        del self.image_path
                        self.pending_command = None
                    else:
                        speak("Sir, on what basis should I analyze this image?")
                        # self.display_message("Enter the description for image analysis:", "JARVIS", False)
                else:
                    description = user_input.strip()
                    # from MainJarvis_TaskExecution import send_to_Gemini
                    response = send_to_Gemini(description, image_path=self.image_path)
                    # self.display_message(response, "JARVIS", False)
                    speak(" Sir, Below is the analysis of the image")
                    print(response)
                    del self.image_path
                    self.pending_command = None

       

     

        elif self.pending_command == "get_schedule":
                user_date = user_input.strip()

                if not user_date:
                    self.display_message("⚠️ Please enter a valid date in YYYY-MM-DD format.", "JARVIS", False)
                    self.pending_command = None
                else:
                    self.pending_command = None
                    from MainJarvis_TaskExecution import fetch_events
                    from datetime import datetime

                    events = fetch_events(user_date)

                    if not events:
                        response = f"No events found for {user_date}."
                    else:
                        response = f"Events on {user_date}:\n"
                        for event in events:
                            summary = event.get('summary', '(No Title)')
                            start_dt = event.get('start', {}).get('dateTime')
                            end_dt = event.get('end', {}).get('dateTime')
                            description = event.get('description', 'No description provided')

                            if start_dt and end_dt:
                                # Convert ISO 8601 time to IST time (formatted)
                                start = datetime.fromisoformat(start_dt).strftime("%I:%M %p")
                                end = datetime.fromisoformat(end_dt).strftime("%I:%M %p")
                            else:
                                start = "All-day Event"
                                end = "Unknown Time"

                            response += f"- {summary} ({start} to {end})\n  {description}\n\n"

                    # Display and speak the final result
                    speak(response.strip())


        elif self.pending_command == "add_event_date":
            event_date = user_input.strip()
            if not event_date:
                self.display_message("⚠️ Please enter a valid date in YYYY-MM-DD format.", "JARVIS", False)
            else:
                self.event_data = {}  # Initialize dict
                self.event_data["date"] = event_date
                self.pending_command = "add_event_summary"
                speak("Now enter the event summary Sir.")
                # self.display_message("📌 Please enter the event summary.", "JARVIS", False)

        elif self.pending_command == "add_event_summary":
            event_summary = user_input.strip()
            if not event_summary:
                self.display_message("⚠️ Event summary cannot be empty.", "JARVIS", False)
            else:
                self.event_data["summary"] = event_summary
                self.pending_command = "add_event_description"
                speak("Now enter the description Sir.")
                # self.display_message("📝 Please enter the event description (optional).", "JARVIS", False)

        elif self.pending_command == "add_event_description":
            event_description = user_input.strip()
            self.event_data["description"] = event_description
            self.pending_command = "add_event_start_time"
            speak("Now enter the start time of event")
            # self.display_message("⏳ Now enter the start time (HH:MM).", "JARVIS", False)

        elif self.pending_command == "add_event_start_time":
            start_time = user_input.strip()
            if not start_time:
                self.display_message("⚠️ Please enter a valid start time (HH:MM).", "JARVIS", False)
            else:
                self.event_data["start_time"] = start_time
                self.pending_command = "add_event_start_am_pm"
                self.display_message("🌞 Is this time in AM or PM? (Enter 'AM' or 'PM')", "JARVIS", False)

        elif self.pending_command == "add_event_start_am_pm":
            start_am_pm = user_input.strip().upper()
            if start_am_pm not in ["AM", "PM"]:
                self.display_message("⚠️ Please enter 'AM' or 'PM'.", "JARVIS", False)
            else:
                self.event_data["start_am_pm"] = start_am_pm
                self.pending_command = "add_event_end_time"
                speak("Now enter the end time of event")
                # self.display_message("⏳ Now enter the end time (HH:MM).", "JARVIS", False)

        elif self.pending_command == "add_event_end_time":
            end_time = user_input.strip()
            if not end_time:
                self.display_message("⚠️ Please enter a valid end time (HH:MM).", "JARVIS", False)
            else:
                self.event_data["end_time"] = end_time
                self.pending_command = "add_event_end_am_pm"
                self.display_message("🌙 Is this time in AM or PM? (Enter 'AM' or 'PM')", "JARVIS", False)

        elif self.pending_command == "add_event_end_am_pm":
            end_am_pm = user_input.strip().upper()
            if end_am_pm not in ["AM", "PM"]:
                self.display_message("⚠️ Please enter 'AM' or 'PM'.", "JARVIS", False)
            else:
                self.event_data["end_am_pm"] = end_am_pm
                self.pending_command = None

                from MainJarvis_TaskExecution import add_event
                response = add_event(self.event_data)

                # self.display_message(response, "JARVIS", False)
                speak(response)

        elif self.pending_command == "delete_event_date":
            event_date = user_input.strip()
            if not event_date:
                self.display_message("⚠️ Please enter a valid date in YYYY-MM-DD format.", "JARVIS", False)
            else:
                self.event_data = {}  # Reinitialize event data
                self.event_data["date"] = event_date
                from MainJarvis_TaskExecution import delete_event_by_summary
                events_list = delete_event_by_summary(event_date, fetch_only=True)

                if not events_list:
                    self.display_message(f"📅 No events found on {event_date}.", "JARVIS", False)
                    self.pending_command = None
                else:
                    self.display_message(f"📋 Events on {event_date}:", "JARVIS", False)
                    for event in events_list:
                        self.display_message(f"🔹 {event}", "JARVIS", False)

                    self.pending_command = "delete_event_summary"
                    speak("Please enter the event summary to delete Sir.")
                    # self.display_message("✏️ Enter the event summary to delete:", "JARVIS", False)

        elif self.pending_command == "delete_event_summary":
            event_summary = user_input.strip()
            if not event_summary:
                self.display_message("⚠️ Event summary cannot be empty.", "JARVIS", False)
            else:
                self.event_data["summary"] = event_summary
                self.pending_command = "delete_event_confirm"
                speak("Are you sure you want to delete?")
                # self.display_message(f"❓ Are you sure you want to delete '{event_summary}'? (yes/no)", "JARVIS", False)

        elif self.pending_command == "delete_event_confirm":
            confirm = user_input.strip().lower()
            if confirm not in ["yes", "no"]:
                self.display_message("⚠️ Please enter 'yes' or 'no'.", "JARVIS", False)
            elif confirm == "no":
                self.display_message("❌ Event deletion canceled.", "JARVIS", False)
            else:
                from MainJarvis_TaskExecution import delete_event_by_summary
                response = delete_event_by_summary(
                    self.event_data["date"],
                    self.event_data["summary"],
                    delete=True
                )
                # self.display_message(response, "JARVIS", False)
                speak(response)

            self.pending_command = None

        elif self.pending_command == "document_extractor":
                file_path = user_input.strip()
                self.pending_command = None
                self.expected_responses = 0

                # speak("Extracting document details, Sir.")
                from Official_Document_Extractor import analyze_official_document # Import function
                response = analyze_official_document(file_path)  # Directly call function
                # speak("Document details extracted successfully and saved in our directory")
                # print(f"Document details saved at: {response}")
                return  # Exit after processing

        elif self.pending_command == "calory_advisor":
                file_path = user_input.strip()
                self.pending_command = None
                self.expected_responses = 0

                # speak("Analyzing food nutrition, Sir.")
                from food_nutritionist import analyze_food_nutrition  # Import function
                response = analyze_food_nutrition(file_path)  # Call function
                # self.display_message(response, "JARVIS", False)
                # speak("Below are the following details captured from food nutrition.")
                # print(response)
                return  # Exit after processing

        elif self.pending_command == "youtube_summary":
                youtube_url = user_input.strip()
                from youtube_video_summarizer import summarize_youtube_video  # Import function
                summary = summarize_youtube_video(youtube_url)
                # self.display_message(summary, "JARVIS", False)
                self.pending_command = None  # Reset state

        elif self.pending_command == "medical_analysis":
                image_path = user_input.strip()
                from Medical_Analysis import analyze_medical_image  # Import function
                report = analyze_medical_image(image_path)
                # self.display_message(report, "JARVIS", False)
                speak("Here is your medical analysis report, Sir.")
                # print(report)
                self.pending_command = None  # Reset state

        elif self.pending_command == "code_debugging":
                user_lang = user_input.strip()
                self.code_debug = []
                self.code_debug.append(user_lang)
                speak("Sir please enter the code to be fixed")
                self.pending_command = "code_debugging1"
                
        elif self.pending_command == "code_debugging1":
            user_code = user_input.strip()
            self.code_debug.append(user_code)
            from Code_debugged import debug_code  # Import function
            report = debug_code(self.code_debug[1], self.code_debug[0].lower()) 
            self.code_debug.clear()  # Clear the list after use
            self.pending_command = None  # Reset state 

        elif self.pending_command == "wikipedia_search":
            topic = user_input.strip()
            from MainJarvis_TaskExecution import wikipedia_search  # Import function
            result = wikipedia_search(topic)
            # self.display_message(result, "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "google_search":
            topic = user_input.strip()
            from MainJarvis_TaskExecution import open_google_search  # Import function
            open_google_search(topic)
            # self.display_message(f"🔍 Google search opened for: {topic}", "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "whatsapp_message_step2":
            # Step 2: Receive message content
            message = user_input.strip()
            number = self.last_input_value  # stored from step 1
            from MainJarvis_TaskExecution import send_whatsapp  # Import function
            send_whatsapp(number, message)
            # self.display_message(f"📤 WhatsApp message sent to {number}.", "JARVIS", False)
            self.pending_command = None
            self.last_input_value = None

        elif self.pending_command == "whatsapp_message":
            # Step 1: Receive number
            number = user_input.strip()
            self.last_input_value = number
            self.pending_command = "whatsapp_message_step2"
            speak("Sir please enter the context of this message?")
            # self.display_message("💬 Please enter the message to send via WhatsApp:", "JARVIS", False)

        elif self.pending_command == "youtube_play":
            topic = user_input.strip()
            from MainJarvis_TaskExecution import play_on_yt  # Import function
            play_on_yt(topic)
            # self.display_message(f"▶️ Playing on YouTube: {topic}", "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "set_alarm":
            alarm_time = user_input.strip()
            from MainJarvis_TaskExecution import set_alarm  # Import function
            set_alarm(alarm_time)
            # self.display_message(f"⏰ Alarm has been set for: {alarm_time}", "JARVIS", False)
            # speak("Alarm has been set, Sir.")
            self.pending_command = None

        elif self.pending_command == "weather":
            city = user_input.strip()
            from MainJarvis_TaskExecution import weather  # Import the function
            weather(city)
            # self.display_message(f"🌍 Fetching weather for: {city}", "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "send_sms":
            msg = user_input.strip()
            from MainJarvis_TaskExecution import send_sms_message
            send_sms_message(msg)
            # self.display_message("📤 Message sent successfully.", "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "voice_call":
            msg = user_input.strip()
            from MainJarvis_TaskExecution import send_voice_call
            send_voice_call(msg)
            # self.display_message("📢 Voice message sent via call.", "JARVIS", False)
            self.pending_command = None

        elif self.pending_command == "assignment":
            self.ass_args = []
            topic = user_input.strip()
            self.ass_args.append(topic)
            speak("Does this assignment include coding and output? (yes/no): ")
            self.pending_command = "code"

        elif self.pending_command == "code":
            ans = user_input.strip().lower()
            self.ass_args.append(ans == "yes")  # Simplified conversion
            speak("Enter any specific requirements or constraints for the assignment:")
            self.pending_command = "instructions"

        elif self.pending_command == "instructions":
            instruction = user_input.strip()
            self.ass_args.append(instruction)
            speak("Enter the LO Mapping text exactly as it should appear in the conclusion:")
            self.pending_command = "lo_map"

        elif self.pending_command == "lo_map":
            lo_map = user_input.strip()
            self.ass_args.append(lo_map)
            speak("Enter the assignment number:")
            self.pending_command = "assignment_number"

        elif self.pending_command == "assignment_number":
            assignment_number = user_input.strip()
            self.ass_args.append(assignment_number)
            
            # ✅ Correct Parameter Order
            import Assignment_Creation

            Assignment_Creation.generate_assignment(
                topic=self.ass_args[0],
                include_code=self.ass_args[1],
                requirements=self.ass_args[2],
                lo_mapping_text=self.ass_args[3],
                assignment_number=self.ass_args[4]
            )
            # speak("Assignment generated successfully, Sir.")
            self.ass_args.clear()
            self.pending_command = None

            # Handle Multi-Step Input (Fallback handler for other ongoing commands)

        elif self.pending_command == "code_generator":
            self.code_gen = []
            task = user_input.strip()
            self.code_gen.append(task)
            speak("Sir, now tell me the programming language.")
            self.pending_command = "language"

        elif self.pending_command == "language":
            lang = user_input.strip().lower()
            # if lang not in language_extensions:
            #     speak(f"Sorry Sir, '{lang}' is not a supported language. Please enter one of the following:")
            #     print(', '.join(language_extensions.keys()))
            #     return  # stay in the same pending state
            self.code_gen.append(lang)
            speak(f"Great. Now, what is your skill level? (Choose from: {', '.join(code_segment.prompt_levels.keys())})")
            self.pending_command = "skill"

        elif self.pending_command == "skill":
            skill = user_input.strip().lower()
            if skill not in code_segment.prompt_levels:
                speak(f"Sorry Sir, '{skill}' is not a valid skill level. Please enter one of: {', '.join(code_segment.prompt_levels.keys())}")
                return  # stay in the same pending state
            self.code_gen.append(skill)
            code_segment.code_generate(self.code_gen[0], self.code_gen[1], self.code_gen[2])  
            self.code_gen.clear()  # Clear the list after use  
            self.pending_command = None

        elif self.pending_command == "document_summary":
            self.doc_summary = []
            file_title = user_input.strip()
            self.doc_summary.append(file_title)
            speak("Sir, please tell me what is this document about:")
            self.pending_command = "document_context"

        elif self.pending_command == "document_context":
            file_document = user_input.strip()
            self.doc_summary.append(file_document)
            speak("Sir, please tell me the purpose of this document(e.g., exam prep, revision, research):")
            self.pending_command = "document_purpose"
        
        elif self.pending_command == "document_purpose":
            file_purpose = user_input.strip()
            self.doc_summary.append(file_purpose)
            speak("Sir, please tell me for whom is this summary(e.g., student, teacher, researcher):")
            self.pending_command = "document_audience"

        elif self.pending_command == "document_audience":
            doc_aud = user_input.strip()
            self.doc_summary.append(doc_aud)
            speak("Now, Please enter the file path of the document:")
            self.pending_command = "document_path"

        elif self.pending_command == "document_path":
            doc_path = user_input.strip()
            self.doc_summary.append(doc_path)
            from document_summarizer import main
            main(self.doc_summary[0],self.doc_summary[1],self.doc_summary[2], self.doc_summary[3], self.doc_summary[4])
            self.doc_summary.clear()
            self.pending_command = None
            
        elif self.pending_command == "generate_image":
            prompt = user_input.strip()
            from image_gen import generate_and_save_image
            generate_and_save_image(prompt)
            self.pending_command = None

        elif self.pending_command == "data_analysis":
            file_path = user_input.strip()
            from jarvis_data_analysis import run_data_analysis
            run_data_analysis(file_path,os.getenv("GEMINI_API_2"))
            self.pending_command = None

        elif self.pending_command == "generate_word":
            choice = user_input.strip().lower()
            if "engin" in choice:
                speak("Sir, please enter the topic of your notes")
                self.engineer_notes = []
                self.pending_command = "detail"
            else:
                speak("Sir, Please enter the topic of your general document")
                self.general_doc = []
                self.pending_command = "audience"

        # ENGINEERING NOTES FLOW
        elif self.pending_command == "detail":
            topic = user_input.strip()
            self.engineer_notes.append(topic)
            speak("Sir please enter the detail level of your notes (basic, intermediate, in-depth)")
            self.pending_command = "concept"

        elif self.pending_command == "concept":
            detailing = user_input.strip()
            self.engineer_notes.append(detailing)
            speak("Sir, what concepts should be specifically more focused? Include concepts in comma-separated form.")
            self.pending_command = "note_format"

        elif self.pending_command == "note_format":
            concepts = user_input.strip()
            self.engineer_notes.append(concepts)
            speak("Sir, What should be the notes format (e.g., Q&A, structured, Paragraph, bullet points):")
            self.pending_command = "file_name"

        elif self.pending_command == "file_name":
            format = user_input.strip()
            self.engineer_notes.append(format)
            speak("Sir, What should be the name of the file?")
            self.pending_command = "execute"

        elif self.pending_command == "execute":
            name = user_input.strip()
            self.engineer_notes.append(name)
            speak("Creating the document from your given information")
            from jarvis_docx_creator import engineering_notes
            engineering_notes(
                self.engineer_notes[0],  # topic
                self.engineer_notes[1],  # detail level
                self.engineer_notes[2],  # concepts
                self.engineer_notes[3],  # format
                self.engineer_notes[4]   # file name
            )
            self.engineer_notes.clear()  # Clear the list after use
            self.pending_command = None

        # GENERAL DOC FLOW
        elif self.pending_command == "audience":
            topic = user_input.strip()
            self.general_doc.append(topic)
            speak("Sir, now please tell the target audience (e.g., student, teacher, researcher)")
            self.pending_command = "purpose"

        elif self.pending_command == "purpose":
            audience = user_input.strip()
            self.general_doc.append(audience)
            speak("Sir, Now please tell the purpose of this document")
            self.pending_command = "Tone"

        elif self.pending_command == "Tone":
            purpose = user_input.strip()
            self.general_doc.append(purpose)
            speak("Sir, what should be the tone of the document (formal, informal, technical):")
            self.pending_command = "pages"

        elif self.pending_command == "pages":
            tone = user_input.strip()
            self.general_doc.append(tone)
            speak("Sir, Please tell me the total number of pages of this document:")
            self.pending_command = "file_naming"

        elif self.pending_command == "file_naming":
            pages = user_input.strip()
            self.general_doc.append(pages)
            speak("Sir, what should be the name of the file:")
            self.pending_command = "GENERATOR"

        elif self.pending_command == "GENERATOR":
            file_name = user_input.strip()
            self.general_doc.append(file_name)
            speak("Sir, generating the document according to your given information.")
            from jarvis_docx_creator import general_docx
            general_docx(
                self.general_doc[0],  # topic
                self.general_doc[1],  # audience
                self.general_doc[2],  # purpose
                self.general_doc[3],  # tone
                self.general_doc[4],  # pages
                self.general_doc[5]   # file name
            )
            self.general_doc.clear()  # Clear the list after use
            self.pending_command = None

        
                    

        elif self.pending_command:
                self.pending_responses.append(user_input)
                if len(self.pending_responses) >= self.expected_responses:
                    full_command = f"{self.pending_command} {' '.join(self.pending_responses)}"
                    self.pending_command = None
                    self.pending_responses = []
                    self.expected_responses = 0
                    self.run_jarvis(full_command)
                return  # Prevent further processing

            # Run Normal Command Processing
        else:
                self.run_jarvis(user_input)

    
    def handle_email_input(self, user_input):
        if not hasattr(self, 'email_data'):
            self.email_data = {}

        if self.email_state == "to":
            self.email_data["to"] = user_input
            self.email_state = "recipient_type"
            speak("Who is the recipient, Sir? For example, friend, boss, parent, teacher, or client?")

        elif self.email_state == "recipient_type":
            self.email_data["recipient_type"] = user_input.strip().lower()
            self.email_state = "tone"
            speak("Should I write the email in formal or informal tone, Sir?")

        elif self.email_state == "tone":
            tone_input = user_input.strip().lower()

            if "informal" in tone_input:
                self.email_data["tone"] = "informal"
            elif "formal" in tone_input:
                self.email_data["tone"] = "formal"
            else:
                self.email_data["tone"] = "informal"  # default fallback
            self.email_state = "context"
            speak("Please tell me the context or purpose of the email.")

        elif self.email_state == "context":
            self.email_data["context"] = user_input

            # ==== Use Gemini to generate email content ====
            subject, message = generate_email_content_with_gemini(
                self.email_data["context"],
                self.email_data["tone"],
                self.email_data["recipient_type"]
            )

            if subject is None:
                self.display_message(message, sender="JARVIS", user=False)
                speak("Sorry sir, there was a problem generating the email.")
                self.email_state = None
                return

            self.email_data["subject"] = subject
            self.email_data["message"] = message

            self.email_state = "file_attach"
            speak("Do you want to attach a file also? Say yes or no.")

        elif self.email_state == "file_attach":
            if "yes" in user_input.lower():
                self.email_state = "file_path"
                speak("Please enter the file path with its extension.")
            else:
                self.send_email_and_reset()

        elif self.email_state == "file_path":
            self.email_data["file_path"] = user_input
            self.send_email_and_reset()



    def handle_insta_input(self, user_input):
        if not hasattr(self, 'insta_username'):
            self.insta_username = ""

        if self.insta_state == "username":
            self.insta_username = user_input
            webbrowser.open(f"https://www.instagram.com/{self.insta_username}")
            speak(f"Sir, here is the profile of user {self.insta_username}.")
            # self.display_message(f"Instagram Profile Opened: {self.insta_username}", "JARVIS", False)

            self.insta_state = "download_pic"
            speak("Sir, would you like to download the profile picture of this account? Say yes or no.")
            # self.display_message("Do you want to download the profile picture? (yes/no):", "JARVIS", False)

        elif self.insta_state == "download_pic":
            if "yes" in user_input.lower():
                self.download_instagram_profile_pic(self.insta_username)
                speak("I am done, sir. Profile pic is saved in our main folder.")
                # self.display_message("Profile picture downloaded successfully!", "JARVIS", False)
            else:
                speak("Alright, not downloading the profile picture.")
                # self.display_message("Skipping profile picture download.", "JARVIS", False)

            self.insta_state = None  # Reset state
            self.insta_username = ""  # Clear username


    def download_instagram_profile_pic(self, username):
        try:
            import instaloader
            mod = instaloader.Instaloader()
            mod.download_profile(username, profile_pic_only=True)
        except Exception as e:
            speak("Sorry Sir. Unable to download the profile picture.")
            self.display_message(f"JARVIS: Error downloading profile picture: {e}", "JARVIS", False)


    def send_email_and_reset(self):
        try:
            from MainJarvis_TaskExecution import sendEmail
            sendEmail(
                to=self.email_data.get("to"),
                subject=self.email_data.get("subject"),
                message=self.email_data.get("message"),
                file_path=self.email_data.get("file_path")
            )
            # speak("Email has been sent successfully, Sir.")
            # self.display_message("✅ Email sent successfully.", sender="JARVIS", user=False)
        except Exception as e:
            self.display_message(f"❌ Error sending email: {e}", sender="JARVIS", user=False)
            speak("Sorry Sir, I was unable to send the email.")

        self.email_state = None
        self.email_data = {}


    def run_jarvis(self, command):
        """Run JARVIS backend in a separate thread."""
        import threading
        threading.Thread(target=self.execute_jarvis_command, args=(command,), daemon=True).start()

    def execute_jarvis_command(self, command):
        self.display_message("⌛ Processing...", "JARVIS", False)
        command = command.lower()

        # ---------------- EMAIL ---------------
        if "open email" in command.lower() or "open my email" in command.lower() or "mail" in command.lower():
            self.email_state = "to"
            speak("Opened your email Sir. To whom should I send the email?")

            # self.display_message("Enter recipient email:", "JARVIS", False)

        # ---------------- INSTAGRAM ---------------
        elif "instagram" in command.lower() or "insta" in command.lower():
            self.insta_state = "username"
            speak("Sir, please enter the Instagram username.")
            # self.display_message("Enter Instagram username:", "JARVIS", False)

        # ---------------- HIDE/UNHIDE FOLDER ---------------
        elif command.lower() == "unhide folder":
            speak("Sir, please type the folder location whose files you want to UNHIDE.")
            # self.display_message("Enter the folder path to unhide files:", "JARVIS", False)
            self.pending_command = "unhide_folder"

        elif command.lower() == "hide folder" or command.lower() == "visible":
            speak("Sir, please type the folder location whose files you want to HIDE.")
            # self.display_message("Enter the folder path to hide files:", "JARVIS", False)
            self.pending_command = "hide_folder"

        # ---------------- COPY FILE ----------------
        elif command.lower() == "copy file":
            speak("Sir, please enter the source file path with extension.")
            # self.display_message("Enter the source file path with extension:", "JARVIS", False)
            self.pending_command = "copy_file_stage1"

        elif self.pending_command == "copy_file_stage1":
            self.source_path = command.strip()
            speak("Sir, please enter the destination file path.")
            # self.display_message("Enter the destination file path:", "JARVIS", False)
            self.pending_command = "copy_file_stage2"

        elif self.pending_command == "copy_file_stage2":
            destination_path = command.strip()
            try:
                from MainJarvis_TaskExecution import copy_file
                copy_file(self.source_path, destination_path)
                # self.display_message("✅ File copied successfully.", "JARVIS", False)
            except Exception as e:
                self.display_message(f"JARVIS: Failed to copy file: {e}", "JARVIS", False)

            self.pending_command = None
            self.source_path = ""

        # ---------------- COPY FOLDER ----------------
        elif command.lower() == "copy folder" or command.lower() == "copy directory":
            speak("Sir, please enter the source folder path.")
            self.display_message("Enter the source folder path:", "JARVIS", False)
            self.pending_command = "copy_folder_stage1"

        elif self.pending_command == "copy_folder_stage1":
            self.source_folder = command.strip()
            speak("Sir, please enter the destination folder path (it must not already exist).")
            self.display_message("Enter the destination folder path:", "JARVIS", False)
            self.pending_command = "copy_folder_stage2"

        elif self.pending_command == "copy_folder_stage2":
            destination_folder = command.strip()
            try:
                from MainJarvis_TaskExecution import copy_folder
                copy_folder(self.source_folder, destination_folder)
                self.display_message("✅ Folder copied successfully.", "JARVIS", False)
            except Exception as e:
                self.display_message(f"JARVIS: Failed to copy folder: {e}", "JARVIS", False)

            self.pending_command = None
            self.source_folder = ""

        # ---------------- MOVE FILE ----------------
        elif command.lower() == "move file":
            speak("Sir, please enter the source file path with extension.")
            self.display_message("Enter the source file path with extension:", "JARVIS", False)
            self.pending_command = "move_file_stage1"

        elif self.pending_command == "move_file_stage1":
            self.source_path = command.strip()
            speak("Sir, please enter the destination file path.")
            self.display_message("Enter the destination file path:", "JARVIS", False)
            self.pending_command = "move_file_stage2"

        elif self.pending_command == "move_file_stage2":
            destination_path = command.strip()
            try:
                from MainJarvis_TaskExecution import move_file
                move_file(self.source_path, destination_path)
                self.display_message("✅ File moved successfully.", "JARVIS", False)
            except Exception as e:
                self.display_message(f"JARVIS: Failed to move file: {e}", "JARVIS", False)

            self.pending_command = None
            self.source_path = ""

        # ---------------- MOVE FOLDER ----------------
        elif command.lower() == "move folder":
            speak("Sir, please enter the source folder path.")
            # self.display_message("Enter the source folder path:", "JARVIS", False)
            self.pending_command = "move_folder_stage1"

        elif self.pending_command == "move_folder_stage1":
            self.source_folder = command.strip()
            speak("Sir, please enter the destination folder path.")
            # self.display_message("Enter the destination folder path:", "JARVIS", False)
            self.pending_command = "move_folder_stage2"

        elif self.pending_command == "move_folder_stage2":
            destination_folder = command.strip()
            try:
                from MainJarvis_TaskExecution import move_folder
                move_folder(self.source_folder, destination_folder)
                # self.display_message("✅ Folder moved successfully.", "JARVIS", False)
            except Exception as e:
                self.display_message(f"JARVIS: Failed to move folder: {e}", "JARVIS", False)

            self.pending_command = None
            self.source_folder = ""

        # ---------------- DELETE FILE ----------------
        elif "delete file" in command.lower():
            speak("Sir, please enter the file path along with its extension.")
            # self.display_message("Enter the file path with extension:", "JARVIS", False)
            self.pending_command = "delete_file"

        elif self.pending_command == "delete_file":
            file_path = command.strip()
            from MainJarvis_TaskExecution import delete_file
            delete_file(file_path)
            # self.display_message("✅ File deleted successfully.", "JARVIS", False)
            self.pending_command = None

        elif "delete folder" in command.lower() or "delete directory" in command.lower():
            speak("Sir, please enter the folder path.")
            # self.display_message("Enter the folder path:", "JARVIS", False)
            self.pending_command = "delete_folder"

        elif self.pending_command == "delete_folder":
            folder_path = command.strip()
            from MainJarvis_TaskExecution import delete_folder
            delete_folder(folder_path)
            # self.display_message("✅ Folder deleted successfully.", "JARVIS", False)
            self.pending_command = None

        elif "archive zip" in command.lower() or "compress folder" in command.lower():
            speak("Sir, please enter the source folder path to archive.")
            # self.display_message("Enter the source folder path to archive:", "JARVIS", False)
            self.pending_command = "archive_zip"

        elif self.pending_command == "archive_zip":
            if not hasattr(self, 'zip_source'):
                self.zip_source = command.strip()
                speak("Sir, please enter the destination folder where you want to save the ZIP file.")
                # self.display_message("Enter the destination folder path:", "JARVIS", False)
            elif not hasattr(self, 'zip_destination'):
                self.zip_destination = command.strip()
                speak("Sir, please enter the name of the ZIP file (without .zip extension).")
                # self.display_message("Enter the ZIP file name:", "JARVIS", False)
            else:
                zip_name = command.strip()
                from MainJarvis_TaskExecution import archive_zip  # Fixed typo from archieve_zip
                archieve_zip(self.zip_source, self.zip_destination, zip_name)
                # self.display_message(f"✅ Folder archived successfully as {zip_name}.zip.", "JARVIS", False)

                del self.zip_source
                del self.zip_destination
                self.pending_command = None

        elif "extract zip" in command.lower():
            speak("Sir, please enter the ZIP file path.")
            # self.display_message("Enter the ZIP file path:", "JARVIS", False)
            self.pending_command = "extract_zip"

        elif self.pending_command == "extract_zip":
            if not hasattr(self, 'zip_file'):
                self.zip_file = command.strip()
                speak("Sir, please enter the destination folder where you want to extract the ZIP file.")
                # self.display_message("Enter the destination folder:", "JARVIS", False)
            else:
                destination_folder = command.strip()
                from MainJarvis_TaskExecution import extract_zip
                extract_zip(self.zip_file, destination_folder)
                # self.display_message("✅ ZIP extracted successfully.", "JARVIS", False)

                del self.zip_file
                self.pending_command = None

        elif "create folder" in command.lower() or "new directory" in command.lower():
            speak("Sir, please enter the folder path where you want to create the new directory along with the folder name included in the path.")
            self.display_message("Enter the folder path:", "JARVIS", False)
            self.pending_command = "create_folder"

        elif self.pending_command == "create_folder":
            folder_path = command.strip()
            from MainJarvis_TaskExecution import create_folder
            create_folder(folder_path)
            self.display_message("✅ Folder created successfully.", "JARVIS", False)
            self.pending_command = None

        elif "create file" in command.lower() or "new file" in command.lower():
            speak("Sir, please enter the full file path including the filename and extension.")
            self.display_message("Enter the full file path with extension:", "JARVIS", False)
            self.pending_command = "create_file"

        elif self.pending_command == "create_file":
            file_path = command.strip()
            from MainJarvis_TaskExecution import create_file
            create_file(file_path)
            self.display_message("✅ File created successfully.", "JARVIS", False)
            self.pending_command = None

        elif "run command" in command.lower() or "execute command" in command.lower() or \
            "run a command" in command.lower() or "execute a command" in command.lower():
            speak("Sir, please enter the command you want to execute.")
            # self.display_message("Enter the command to execute:", "JARVIS", False)
            self.pending_command = "execute_system_command"

        elif self.pending_command == "execute_system_command":
            command = command.strip()

            if "rmdir /s" in command.lower():
                # Ensure correct syntax & replace with 'rmdir /q /s'
                parts = command.split("rmdir /s", 1)
                if len(parts) > 1:
                    folder_path = parts[1].strip()
                    if not (folder_path.startswith('"') and folder_path.endswith('"')):
                        folder_path = f'"{folder_path}"'  # Ensure quotes around folder path
                    command = f"rmdir /q /s {folder_path}"  # Add /q silently

                speak("Sir, are you sure you want to delete this folder? Type 'Y' to confirm or 'N' to cancel.")
                # self.display_message("⚠️ WARNING: Type 'Y' to confirm deletion or 'N' to cancel:", "JARVIS", False)
                self.pending_command = "confirm_rmdir"
                self.stored_command = command  # Store the command
            else:
                from MainJarvis_TaskExecution import execute_system_command  # Import function
                result = execute_system_command(command)
                self.display_message(result, "JARVIS", False)
                self.pending_command = None  # Reset state

        elif self.pending_command == "confirm_rmdir":
            confirmation = command.strip().lower()
            if confirmation == "y" and hasattr(self, "stored_command"):
                from MainJarvis_TaskExecution import execute_system_command
                result = execute_system_command(self.stored_command)  # Execute stored command
                self.display_message(result, "JARVIS", False)
                del self.stored_command  # Clean up
            else:
                self.display_message("❌ Command discarded. Folder was NOT deleted.", "JARVIS", False)
                if hasattr(self, "stored_command"):
                    del self.stored_command

            self.pending_command = None  # Reset state

        elif "check health" in command.lower() or "medical" in command.lower():
            speak("Sir, please provide the image path for medical analysis.")
            # self.display_message("🩺 Enter the image path for medical analysis:", "JARVIS", False)
            self.pending_command = "medical_analysis"

        elif "generate image" in command.lower() or "generate an image" in command.lower():
            speak("Sir, Please enter the prompt to generate its image")
            self.pending_command = "generate_image"

        elif "image" in command.lower() or "picture" in command.lower() or "photo" in command.lower():
            speak("Sir, please enter the full file path of the image to perform its analysis.")
            # self.display_message("Enter the full file path of the image:", "JARVIS", False)
            self.pending_command = "image_analysis"

        elif self.pending_command == "image_analysis":
            if not hasattr(self, 'image_path'):
                self.image_path = command.strip()
                speak("Sir, on what basis should I analyze this image?")
                # self.display_message("Enter the description for image analysis:", "JARVIS", False)
            else:
                description = command.strip()
                response = send_to_Gemini(description, image_path=self.image_path)
                self.display_message(response, "JARVIS", False)
                speak(response)

                del self.image_path  # Clean up
                self.pending_command = None  # Reset state

        # elif "stock price" in command.lower() or "market data" in command.lower() or "share value" in command.lower():
        #     speak("Sir, please enter the stock symbol.")
        #     # self.display_message("📈 Enter the stock symbol:", "JARVIS", False)
        #     self.pending_command = "get_stock_info"

        # elif "crypto" in command or "cryptocurrency price" in command or "coin price" in command:
        #     speak("Sir, please enter the cryptocurrency name.")
        #     # self.display_message("💰 Enter the cryptocurrency name:", "JARVIS", False)
        #     self.pending_command = "get_crypto_price"  # ✅ Start with "get_crypto_price"

        elif "delete event" in command.lower() or "remove event" in command.lower():
            self.event_data = {}
            speak("Sir, on which date should I check for events to delete? Please enter in YYYY-MM-DD format.")
            # self.display_message("📅 Enter the event date (YYYY-MM-DD):", "JARVIS", False)
            self.pending_command = "delete_event_date"

        elif "add event" in command.lower() or "schedule event" in command.lower():
            self.event_data = {}
            speak("Sir, on which date should I add this event? Please enter in YYYY-MM-DD format.")
            # self.display_message("📅 Enter the event date (YYYY-MM-DD):", "JARVIS", False)
            self.pending_command = "add_event_date"

        elif "my events" in command.lower() or "calendar" in command.lower():
            speak("Sir, kindly provide the date in YYYY-MM-DD format.")
            # self.display_message("📅 Enter the date (YYYY-MM-DD):", "JARVIS", False)
            self.pending_command = "get_schedule"

        elif "video" in command.lower():
            speak("Sir, please enter the YouTube video link for summarization process.")
            # self.display_message("🔗 Enter the YouTube video link:", "JARVIS", False)
            self.pending_command = "youtube_summary"

        elif "summarize" in command.lower() or "summary" in command.lower():
            speak("Sir, Please enter the title of the document")
            self.pending_command = "document_summary"

        elif "document" in command.lower():
            speak("Sir, please enter the full file path along with the extension of the image of the document.")
            # self.display_message("Enter the document file path:", "JARVIS", False)
            self.pending_command = "document_extractor"
            self.expected_responses = 1

        elif "calor" in command.lower() or "nutrition" in command.lower() or "meal" in command.lower() or "food" in command.lower():
            speak("Sir, please enter the full file path along with the extension of the food image.")
            # self.display_message("Enter the food image file path:", "JARVIS", False)
            self.pending_command = "calory_advisor"
            self.expected_responses = 1

        elif "youtube" in command.lower() or "music" in command.lower() or "song" in command.lower():
            speak("Sir, please type what you want me to play on YouTube.")
            # self.display_message("🎵 Type what you'd like me to play on YouTube:", "JARVIS", False)
            self.pending_command = "youtube_play"

        

        elif "debug code" in command.lower() or "fix my code" in command.lower():
            speak("Sir, please tell me the language of the code to be debugged.")
            # self.display_message("🛠️ Paste the code you want me to debug:", "JARVIS", False)
            self.pending_command = "code_debugging"

        elif "code" in command.lower() or "program" in command.lower() or "script" in command.lower():
            speak("Sir, Please enter the code description:")
            self.pending_command = "code_generator"

        elif "wiki" in command.lower():
            speak("Sir, please type what you want me to search on Wikipedia.")
            # self.display_message("📘 Enter the topic to search on Wikipedia:", "JARVIS", False)
            self.pending_command = "wikipedia_search"

        elif "google" in command.lower():
            speak("Sir, please type what you want to search on Google.")
            self.pending_command = "google_search"

        elif "whatsapp" in command.lower() or "whats app" in command.lower():
            speak("Sir, please enter the recipient's number with country code")
            self.display_message("📱 Enter WhatsApp number (with country code)(e.g., +919999999999):", "JARVIS", False)
            self.pending_command = "whatsapp_message"

        elif "alarm" in command.lower():
            speak("Sir, please type the time for the alarm. Follow this Time format only: e.g., 5:30 AM")
            # self.display_message("⏰ Enter the alarm time (e.g., 5:30 AM):", "JARVIS", False)
            self.pending_command = "set_alarm"

        elif "weather" in command.lower() or "temperature" in command.lower():
            speak("Please type the name of the city only to get its weather.")
            self.display_message("🌦️ Enter city name only.(e.g., Mumbai):", "JARVIS", False)
            self.pending_command = "weather"

        elif "message" in command.lower() or "send sms" in command.lower():
            speak("Sir, Please enter the context of the SMS to be sent.")
            # self.display_message("✉️ Type the message you want to send:", "JARVIS", False)
            self.pending_command = "send_sms"

        elif "call" in command.lower() or "voice call" in command.lower():
            speak("Please enter the context of the voice message to be delivered, Sir?")
            # self.display_message("📞 Type the voice message for the call:", "JARVIS", False)
            self.pending_command = "voice_call"

        elif "assignment" in command.lower() or "homework" in command.lower():
            speak("Sir, Please enter your assignment topic.")
            self.pending_command = "assignment"

        elif "data analysis" in command.lower():
            speak("Sir, please enter the full CSV path for its analysis")
            self.pending_command = "data_analysis"

        elif "generate word" in command.lower() or "generate docx" in command.lower():
            speak("Sir do you want to generate a general word file or word file for engineering notes?")
            self.pending_command = "generate_word"


        elif any(kw in command.lower() for kw in ["goodbye", "shutdown"]):
            speak("Thanks for using me Sir. Have a wonderful day ahead!")
            # self.display_message("JARVIS", "✨ Thank you, Sir. Have a wonderful day ahead!")
            self.after(1000, self.destroy)  # 👈 Trigger window fade-out after 1 second
            return


        elif command.lower():
            try:
                from MainJarvis_TaskExecution import Task_Execution
                response = Task_Execution(command)
                if response and response.strip():
                    self.display_message(f"{response}", "JARVIS", False)
            except ImportError:
                self.display_message("❌ Error: MainJarvis_TaskExecution module not found.", "JARVIS", False)
            except Exception as e:
                self.display_message(f"⚠️ JARVIS encountered an error while processing: {str(e)}", "JARVIS", False)


        else:
            # Handle unknown command or waiting for input of a previous pending command
            if self.pending_command:
                self.display_message("⚠️ Waiting for required input to complete the previous task...", "JARVIS", False)
            else:
                self.display_message("❌ Sorry, I did not understand the command.", "JARVIS", False)

    def update_time_date(self):
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("🕒 %H:%M:%S"))
        self.date_label.configure(text=now.strftime("📅 %d %B %Y"))
        self.after(1000, self.update_time_date)

    def animate_mic_button(self):
        current = self.mic_button.cget("fg_color")
        next_color = self.ACCENT_COLOR if current == self.BUTTON_COLOR else self.BUTTON_COLOR
        self.mic_button.configure(fg_color=next_color)
        self.after(400, self.animate_mic_button)

    def initial_greet(self):
        greet()
        self.display_message("System Activated. Awaiting your command...", "JARVIS")

    def update_gui(self):
        """Update chat display with new messages from stdout."""
        self.redirector.update_display()
        self.after(100, self.update_gui)



    def generate_llm_response(self, user_input):
        self.show_typing_indicator()
        time.sleep(1.5)  # Simulate thinking delay
        self.hide_typing_indicator()
        response = f"LLM response to: '{user_input}'"
        self.display_message(response, "JARVIS")
        self.add_to_history(response, "JARVIS")

    def show_typing_indicator(self):
        if not hasattr(self, 'typing_label') or self.typing_label is None:
            self.typing_label = ctk.CTkLabel(
                self.chat_display,
                text="JARVIS is typing...",
                text_color="#888888",
                font=self.TEXT_FONT
            )
            self.typing_label.pack(pady=(5, 0), padx=10, anchor="w")

    def hide_typing_indicator(self):
        if hasattr(self, 'typing_label') and self.typing_label is not None:
            self.typing_label.destroy()
            self.typing_label = None

   

    def display_message(self, message, sender, user=False):
        bubble_color = self.JARVIS_BUBBLE_COLOR if sender == "JARVIS" else self.USER_BUBBLE_COLOR
        text_color = self.ACCENT_COLOR if sender == "JARVIS" else self.USER_MSG_COLOR
        anchor = "w" if sender == "JARVIS" else "e"

        bubble = ctk.CTkFrame(self.chat_display, fg_color=bubble_color, corner_radius=15)
        bubble.pack(pady=5, padx=10, anchor=anchor)

        label = ctk.CTkLabel(
            bubble,
            text=message,
            text_color=text_color,
            font=self.TEXT_FONT,
            wraplength=400,
            justify="left"
        )
        label.pack(padx=10, pady=5, ipadx=10, ipady=5)

        self.chat_display.update_idletasks()
        self.chat_display._parent_canvas.yview_moveto(1.0)  # Auto-scroll to the bottom

        self.add_to_history(message, sender)

    def add_to_history(self, message, sender):
        self.history_listbox.configure(state="normal")
        self.history_listbox.insert("end", f"{sender}: {message}\n")
        self.history_listbox.see("end")
        self.history_listbox.configure(state="disabled")

    def clear_history(self):
        self.history_listbox.configure(state="normal")
        self.history_listbox.delete("1.0", "end")
        self.history_listbox.configure(state="disabled")

  
    def open_file_dialog(self):
        try:
            # Let user select file or type a folder path in top bar
            path = filedialog.askopenfilename()

            if path:
                if os.path.isfile(path):
                    # A file was selected
                    self.input_box.delete(0, "end")
                    self.input_box.insert(0, path)
                    # self.display_message(f"📁 Selected file: {path}", "You")
                    # self.add_to_history(path, "You")

                elif os.path.isdir(path):
                    # User typed a folder path in the top bar and hit Enter
                    self.input_box.delete(0, "end")
                    self.input_box.insert(0, path)
                    # self.display_message(f"📂 Selected folder: {path}", "You")
                    # self.add_to_history(path, "Action")

                else:
                    # Neither file nor folder (e.g. invalid path typed)
                    self.display_message("❌ Selected path is invalid.", "System")

        except Exception as e:
            self.display_message(f"❌ File dialog error: {e}", "System")




    def start_voice_input(self):
            self.mic_button.configure(state=ctk.DISABLED, text="...")
            threading.Thread(target=self.voice_input_thread, daemon=True).start()

    def voice_input_thread(self):
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    self.display_message("Listening...", "System")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)
                    self.display_message(command, "You")
                    self.add_to_history(command, "You")
                    self.generate_llm_response(command)
            except Exception as e:
                self.display_message(f"Voice input error: {e}", "System")
            finally:
                self.mic_button.configure(state=ctk.NORMAL, text="🎤")

    def update_system_info(self):
            try:
                battery = psutil.sensors_battery()
                battery_percent = f"{battery.percent:.0f}%" if battery else "N/A"
                cpu_percent = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                ram_percent = f"{ram.percent:.0f}%"
                disk = psutil.disk_usage('/')
                disk_percent = f"{disk.percent:.0f}%"

                self.battery_label.configure(text=f"Battery: {battery_percent}")
                self.cpu_label.configure(text=f"CPU: {cpu_percent}%")
                self.ram_label.configure(text=f"RAM: {ram_percent}")
                self.disk_label.configure(text=f"Disk: {disk_percent}")
            except Exception as e:
                print(f"Error updating system info: {e}")
            self.after(2000, self.update_system_info)

    def load_boot_log(self):
            boot_messages = [
                "System Booting...",
                f"Kernel initialized at {datetime.now().strftime('%H:%M:%S')}",
                "Loading drivers...",
                "Network services started.",
                "User session initiated.",
                "Ready."
            ]

            self.boot_log_textbox.configure(state=ctk.NORMAL)
            for msg in boot_messages:
                self.boot_log_textbox.insert(ctk.END, msg + "\n")
            self.boot_log_textbox.configure(state=ctk.DISABLED)

if __name__ == "__main__":
    app = JarvisChatApp()
    app.mainloop()