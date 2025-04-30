import pyttsx3
import speech_recognition as sr
import os
import subprocess
import screen_brightness_control as sbc
import cv2
from datetime import datetime, timezone, timedelta
import shutil
from requests import get
import requests
import keyboard
import wikipedia
from serpapi import GoogleSearch
import webbrowser
import pywhatkit
import smtplib
import google.generativeai as genai
import re
import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import sys
import pyjokes
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs
import time
# import pygame
import mimetypes
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading
import pyautogui
import instaloader
import pytz
import PyPDF2
import psutil
import speedtest
from twilio.rest import Client
# import google.generativeai as genai
# Importing gemini's API key-:
from PIL import Image
import google.generativeai as genai
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from MainJarvis_TaskExecution import speak





medical_prompt = '''
You are a medical expert and a great doctor. Analyze the image and give a brief medical overview.

Include:
1. Likely diagnosis
2. Key symptoms visible
3. Possible cause
4. Next action (e.g., see doctor, tests, remedies)
5. Urgency (1-5)

Keep it  very detailed, clear, and without markdown. Mention assumptions if unsure.
At the end add a disclaimer: "This is not a medical diagnosis. Always consult a healthcare professional."
'''


def analyze_medical_image(image_path):
        
    GEMINI_API_KEY =os.getenv("GEMINI_API_3") # Replace with your actual key
    genai.configure(api_key=GEMINI_API_KEY)


    # Initialize Gemini chat model
    model = genai.GenerativeModel("gemini-1.5-pro")
    chat_session = model.start_chat(history=[  # Corrected history format
        {"role": "user", "parts": ["You are JARVIS from IRONMAN, an advanced AI assistant. You were created by a team of four: Omkar, Rishi, Suhani, and Sonal. Also act like JARVIS only. When you are asked about any real time query then say-:'Unable to give you real-time data'."]}
    ])
    """Analyzes a medical image and saves a detailed report as a timestamped Word document."""

    if not os.path.exists(image_path):
        speak("❌ Sorry Sir, the specified image file does not exist. Please provide a valid path.")
        return

    try:
        speak("Analyzing the medical image sent by you.")
        # Open and prepare image
        img = Image.open(image_path).convert('RGB')

        # Send to Gemini
        response = model.generate_content([medical_prompt, img])

        if response and response.text:
            report_text = response.text.strip()

            # Create a Word document
            doc = Document()
            doc.add_heading('🩺 Medical Image Analysis Report', 0)

            # Add image for reference (optional)
            try:
                doc.add_picture(image_path, width=Inches(4.5))  # Adjust width as needed
            except:
                doc.add_paragraph("(Image could not be embedded in the report)")

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            doc.add_paragraph(f"📅 Date of Analysis: {timestamp}")

            # Add analysis text
            doc.add_paragraph(report_text)

            # Save with timestamped filename
            safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Medical_Report_{safe_timestamp}.docx"
            report_path = os.path.join(os.getcwd(), filename)
            doc.save(report_path)

            speak(f"Sir, the medical report has been successfully generated and saved in our directory.")
            print(f"report saved as {filename}")
            speak("Attempting to open the file")
            os.startfile(report_path)
            return report_path
        else:
            speak("❌ Sorry Sir, I was unable to analyze the medical image.")
            return

    except Exception as e:
        print(e)
        speak("❌ An error occurred while analyzing the medical image.")
        return

if __name__ == "__main__":
    path =input("Enter path:")
    analyze_medical_image(path)