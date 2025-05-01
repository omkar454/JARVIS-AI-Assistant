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




engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voices', voices[0].id)


# AIzaSyA9rXpMPWsin8919flafhK9x8fHlxWYHBA
speech_rate = engine.getProperty('rate')  # Get the current rate
# AIzaSyBnyH1bGQq5T1DXh_Nirv8rA9LAJi7Kcuc
# Set up Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_1") # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)


# Initialize Gemini chat model
model = genai.GenerativeModel("gemini-1.5-pro")
chat_session = model.start_chat(history=[  # Corrected history format
    {"role": "user", "parts": ["You are JARVIS from IRONMAN, an advanced AI assistant. You were created by a team of four: Omkar, Rishi, Suhani, and Sonal. Also act like JARVIS only. When you are asked about any real time query then say-:'Unable to give you real-time data'."]}
])

def wikipedia_search(query):
     speak("Searching Wikipedia for " + query)
     try:
        if not query:
                                speak("Sorry, I did not catch that. Please type the topic again")
        else:
                            results = wikipedia.summary(query, sentences = 2)
                            speak("According to Wikipedia,")
                            speak(results)
     except Exception as e:
          print(e)
          speak("Sorry Sir, I am unable to search this topic on Wikipedia. Please try again later")


def adjust_speech_rate(command):
    global speech_rate
    try:
        # Inform the user about the valid range
        speak("Sir, Speech rate will always be between 100 and 300.")

        if "increase" in command or "higher" in command:
            speech_rate += 25  # Increase speed
        elif "decrease" in command or "lower" in command:
            speech_rate -= 25  # Decrease speed
        elif "reset" in command or "default" in command or "initial" in command:
            speech_rate = 200  # Reset to default rate

        # Check if the speech rate is out of range
        if speech_rate < 100 or speech_rate > 300:
            speak("Warning: Speech rate must be between 100 and 300. Adjusting to the nearest valid value.")
        
        # Enforce limits
        speech_rate = max(100, min(speech_rate, 300))  
        
        engine.setProperty('rate', speech_rate)
        speak(f"Speech rate adjusted to: {speech_rate}")

    except Exception as e:
        speak("Sorry Sir.Unable to adjust the speech rate of our system. Please try again after some time")
        print(e)

def search_serp_api(query):
    """Fetch real-time search results using SERP API and return a highly accurate response."""
    params = {
        "q": query + " latest news",  # ✅ Append "latest news" to improve relevance
        "hl": "en",
        "gl": "in",
        "api_key": os.getenv("SERP_API")  # Secure API key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" in results and len(results["organic_results"]) > 0:
        top_results = results["organic_results"][:5]  # ✅ Fetch top 5 results
        filtered_results = []

        # ✅ Trusted News Sources for Accuracy
        trusted_sources = ["bbc.com", "reuters.com", "ndtv.com", "espncricinfo.com", "timesofindia.indiatimes.com",
                           "aljazeera.com", "cnn.com", "theguardian.com", "indianexpress.com", "moneycontrol.com"]

        for res in top_results:
            title = res.get('title', 'No title available')
            link = res.get('link', 'No link available')
            snippet = res.get('snippet', 'No summary available.')

            # ✅ Prioritize Trusted Sources Only
            if any(source in link for source in trusted_sources):
                filtered_results.append(f"{title}: {snippet} More details: {link}")

        # ✅ Step 2: If trusted sources found, return the first reliable result
        if filtered_results:
            return filtered_results[0]

        # ✅ Step 3: If no trusted source found, return the best available result
        else:
            first_result = top_results[0]
            return f"{first_result['title']}: {first_result['snippet']} More details: {first_result['link']}"

    else:
        return "Sorry Sir, I couldn't find any real-time results."



def ask_gemini_with_serp(query):
    """Fetch real-time data and ask Gemini to rephrase it conversationally."""
    serp_result = search_serp_api(query)

    # If no real-time data is found, return a default response
    if "Sorry Sir" in serp_result:
        return serp_result

    gemini_prompt = f"Summarize this information conversationally: {serp_result}"
    response = send_to_Gemini(input_text=gemini_prompt)

    return response

def is_real_time_query(query):
    """Check if the query requires real-time information."""
    real_time_keywords = [
        "latest", "news", "current", "weather", "live", "trending",
        "today", "breaking", "happening now", "recent", "update",
        "real-time", "newest", "forecast", "score", "events", "next","tommorow"
    ]

    for word in real_time_keywords:
        if word in query.lower():
            return True

    # Advanced detection for phrases
    if re.search(r"(news|update|forecast|score|event).*(today|now|current|latest|live)", query, re.IGNORECASE):
        return True

    return False

# Function to send query to Gemini API
def send_to_Gemini(input_text=None, image_path=None, serp_data=None):
    """Send query to Gemini. If SERP API data is available, Gemini rephrases it. 
       If Gemini detects a real-time query, it asks the user before using SERP API.
       Also handles image input for Gemini Vision.
    """
    try:
        image_data = None  # Initialize image_data variable

        # ✅ If SERP API data is provided, format it properly for Gemini
        if serp_data:
            gemini_prompt = f"""
            The following is the latest real-time information retrieved from a trusted source:
            {serp_data}
            
            Your task is to rephrase this information in a natural, human-like way without adding any extra details or making up information. 
            Do NOT generate your own facts. Just present the given information in an engaging manner.
            """
            response = model.generate_content(gemini_prompt)
            return response.text.strip()

        # ✅ If an image path is provided, validate and open the image
        if image_path:
            if not os.path.exists(image_path):
                return "Sorry Sir. The specified image file does not exist. Please provide a valid path."
            try:
                img = Image.open(image_path)
                image_data = img  # Store the image
            except FileNotFoundError:
                return "Sorry Sir. Unable to locate the image file. Please check the name and try again."
            except Image.UnidentifiedImageError:
                return "Sir, the file format is invalid. Please provide an image with a valid extension."
            except Exception as e:
                print(f"Error opening image: {e}")
                return "Sorry Sir. Unable to open and read the image. Please try again later."

        # ✅ If both text and image are provided, send both to Gemini
        if input_text and image_data:
            response = model.generate_content([input_text, image_data])
        elif image_data:
            response = model.generate_content(image_data)
        elif input_text:
            response = chat_session.send_message(input_text)
        else:
            return "Please provide either text or an image and try again, Sir."

        # ✅ If Gemini mistakenly gets a real-time query, ask the user for SERP API search
        if "real-time data" in response.text.lower() or "current information" in response.text.lower():
           
                speak("Searching the internet for real-time information, Sir.")
                serp_data = search_serp_api(input_text)  # Fetch real-time data
                response = send_to_Gemini(serp_data=serp_data)  # Send to Gemini for rephrasing
                return response

           

        # ✅ Save conversation history for chat continuity
        user_message = {}
        if input_text and image_data:
            user_message = {"role": "user", "parts": [input_text, image_data]}
        elif input_text:
            user_message = {"role": "user", "parts": [input_text]}
        elif image_data:
            user_message = {"role": "user", "parts": [image_data]}

        if user_message:
            chat_session.history.append(user_message)

        chat_session.history.append({"role": "model", "parts": [response.text.strip()]})

        return response.text.strip()

    except Exception as e:
        print(f"Error: {e}")
        return "I'm experiencing technical difficulties at the moment. So I am unable to respond to your query."
    
# Function to take INPUT from USER-:
def takeCommand():
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
            return takeCommand()  # Retry
        
        except sr.RequestError:
            speak("I am unable to connect to the speech recognition service. Please check your internet connection.")
            speak("Sir, First fix this issue and then rerun me again. So, for now I am leaving Sir. Goodbye")
            sys.exit() 
        
        except sr.WaitTimeoutError:
            speak("You did not say anything. Please say something Sir.")
            return takeCommand()  # Retry
        
        except OSError:
            speak("Sir, I cannot access the microphone. Please check if it is connected.")
            speak("Sir, First fix this issue and then rerun me again. So, for now I am leaving Sir. Goodbye")
            sys.exit() 
        
        except Exception as e:
            speak("Sorry Sir. Unable to recognize your voice. Please say it again.")
            print(f"Error: {e}")
            return takeCommand()  # Retry

def WakeUp_Command():
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
            return "I did not catch that"  # Retry
        
        except sr.RequestError:
            speak("I am unable to connect to the speech recognition service. Please check your internet connection.")
            speak("Sir, First fix this issue and then rerun me again. So, for now I am leaving Sir. Goodbye")
            sys.exit() 
        
        except sr.WaitTimeoutError:
            return "You did not say anything. Please say something Sir."  # Retry
        
        except OSError:
            speak("Sir, I cannot access the microphone. Please check if it is connected.")
            speak("Sir, First fix this issue and then rerun me again. So, for now I am leaving Sir. Goodbye")
            sys.exit() 
        
        except Exception as e:
            return "try try but dont cry"  # Retry


# Function to greet the User
def greet():
    # Get the current hour and minute
    hour = int(datetime.now().hour)
    minute = int(datetime.now().minute)
    
    # Determine the greeting based on the time of day
    if hour >= 0 and hour < 12:
        greeting = "Good Morning Sir"
        time_of_day = "in the morning"
    elif hour >= 12 and hour < 18:
        greeting = "Good Afternoon Sir"
        time_of_day = "in the afternoon"
    else:
        greeting = "Good Evening Sir"
        time_of_day = "in the evening"
    
    # Format the current time
    current_time = f"{hour % 12}:{minute:02d}"  # 12-hour format (e.g., 3:30)
    
    # Construct the full greeting with time
    speak(f"{greeting}, it's {current_time} {time_of_day}")
    
    # Offer help after the greeting
    speak("Welcome Back Sir. Nice to see you again. I am JARVIS. Please tell me how can I help you")

# qkms cgjx dsfc mcpk

# Function to send an Email-:
def sendEmail(to, subject, message, file_path=None):
    try:
        # Speak confirmation (optional - keep if you want voice feedback)
        speak("Sending the email now, Sir.")

        # Setup the email headers and content
        msg = MIMEMultipart()
        msg['From'] = 'omraut41105@gmail.com'
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Handle attachment if provided
        if file_path:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                attachment = open(file_path, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}",
                )
                msg.attach(part)
            else:
                speak("The provided file path is invalid. Sending the email without attachment.")
        
        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login('omraut41105@gmail.com', os.getenv("EMAIL_PASSWORD"))  # Use App Password
        server.sendmail('omraut41105@gmail.com', to, msg.as_string())
        server.close()
        speak("Email has been sent succesfully Sir")
        webbrowser.open("https://mail.google.com/mail/u/1/#sent")

        # speak("Email sent successfully, Sir.")
    
    except Exception as e:
        print(f"JARVIS: Error sending email: {e}")
        speak("Sorry Sir, I was unable to send the email.")
               

# Function to convert TEXT to SPEECH-:
def speak(audio):
    """Returns the spoken text instead of just printing it."""
    print(audio)
    engine.say(audio)
    engine.runAndWait()
    return audio  # Return the text after speaking



def copy_file(source, destination):
            try:
                    shutil.copy(source, destination)
                    os.startfile(destination)
                    time.sleep(2)
                    speak("File copied successfully")
            except FileNotFoundError as fn:
                    speak("Sorry Sir. Unable to locate your file.")
                    print(fn)
            except Exception as e:
                    speak("Sorry Sir. Due to some reasons unable to copy the file. Please try again later.")
                    print(e)    
        
def copy_folder(source, destination):
            try:
                    shutil.copytree(source, destination)
                    os.startfile(destination)
                    time.sleep(2)
                    speak("All the content within source folder is succesfully copied to the destination folder")

            except Exception as e:
                    speak("Sorry Sir. Due to some reasons unable to copy the Directory. Please try again later and Please ensure that the destination path should be NON-EXISTENT only.")
                    print(e)

def move_file(source, destination):
            try:
                    shutil.move(source, destination)
                    os.startfile(destination)
                    time.sleep(2)
                    speak("File moved successfully")
            except Exception as e:
                    speak("Sorry Sir due to some reasons unable to move this file. Please try again later.")
                    print(e)

def move_folder(source, destination):
            try:
                    shutil.move(source, destination)
                    os.startfile(destination)
                    time.sleep(2)
                    speak("Sir, Folder has been moved successfully")
            except Exception as e:
                    speak("Sorry Sir due to some reasons unable to move this directory. Please try again later.")
                    print(e)


# Function to get detailed information about a specific process by PID
def get_process_info(pid):
    """ Fetch and display detailed information about a specific process by PID """
    try:
        process = psutil.Process(pid)  # Get process object
        memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert bytes to MB
        cpu_usage = process.cpu_percent(interval=0.1)  # Get CPU usage
        status = process.status()  # Get process status

        process_info = (
            f"Process Info -\n"
            f"PID: {pid}\n"
            f"Name: {process.name()}\n"
            f"Status: {status}\n"
            f"Memory Usage: {memory_usage:.2f} MB\n"
            f"Memory Percent: {process.memory_percent():.2f}%\n"
            f"CPU Usage: {cpu_usage}%"
        )

        speak(process_info)  # Speak in JARVIS

    except psutil.NoSuchProcess:
        speak(f"Process with PID {pid} not found.")
    except Exception as e:
        speak(f"Not able to give you detailed info of process with PID: {pid}.An error occurred: {str(e)}")


def increase_brightness(steps=50):
        current_brightness = sbc.get_brightness()[0]  # Get current brightness
        new_brightness = min(100, current_brightness + steps)  # Increase brightness, max 100%
        sbc.set_brightness(new_brightness)  # Set new brightness
        
        speak("System Brightness Increased Successfully, Sir.")



def decrease_brightness(steps=50):
   
        current_brightness = sbc.get_brightness()[0]  # Get current brightness
        new_brightness = max(0, current_brightness - steps)  # Decrease brightness, min 0%
        sbc.set_brightness(new_brightness)  # Set new brightness
        
        speak("System Brightness Decreased Successfully, Sir.")

def send_whatsapp(number, context):
    try:
        if not context:
            speak("I did not catch the context. Please try again later.")
            return

        speak("Generating the message based on your context Sir.")

        # Generate refined message directly here
        prompt = f"Write a WhatsApp message based on this context: {context}"
        try:
            response = model.generate_content(prompt)
            refined_message = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")
            speak("Sorry Sir. Could not rephrase the message. Please try again later")
            return

        if refined_message:
            speak("Sending the message now Sir...")
            pywhatkit.sendwhatmsg_instantly(number, refined_message)
            speak("Message sent successfully.")
            print(f"📤 WhatsApp message sent to {number}:\n{refined_message}")
            time.sleep(3)
        else:
            speak("Gemini did not return a valid message. Please try again later Sir..")

    except Exception as e:
        print(e)
        speak("Sorry Sir. Unable to send the message. Please try again later.")




def delete_file(file_path):
              try:
                    
                    if os.path.exists(file_path):
                        parent_directory = os.path.dirname(file_path)  # Get parent directory

                        try:
                            os.remove(file_path)
                            speak("File deleted successfully")
                        except PermissionError:
                            speak("Permission error detected. Attempting forceful deletion.")
                            cmd = f'powershell.exe Remove-Item -Path "{file_path}" -Force'
                            subprocess.run(cmd, shell=True)
                            
                            # Check if file is deleted
                            if os.path.exists(file_path):
                                speak("Failed to delete the file forcefully. Please check permissions.")
                                return
                            else:
                                speak("File forcefully deleted successfully")

                        # Open the parent directory for confirmation
                        if os.path.exists(parent_directory):
                            speak(f"Opening Parent directory of the file for confirmation.")
                            os.startfile(parent_directory)

                    else:
                        speak("The specified file does not exist.")

              except Exception as e:
                    speak("Sorry Sir, due to some reasons I was unable to delete this file. Please try again later.")
                    print(e)
              
def delete_folder(directory_path):
            try:
                    

                    if os.path.exists(directory_path):
                        parent_directory = os.path.dirname(directory_path)  # Get parent directory

                        try:
                            shutil.rmtree(directory_path)
                            speak("Directory deleted successfully")
                        except PermissionError:
                            speak("Access Denied to delete the Directory: Trying to delete directory and its files forcefully...")
                            os.system(f'rmdir /s /q "{directory_path}"')

                            # Check if directory is deleted
                            if os.path.exists(directory_path):
                                speak("Failed to delete the directory forcefully. Please check permissions.")
                                return
                            else:
                                speak("Directory forcefully deleted successfully.")

                        # Open the parent directory for confirmation
                        if os.path.exists(parent_directory):
                            speak(f"Opening the folders parent directory for confirmation.")
                            os.startfile(parent_directory)

                    else:
                        speak("The specified directory does not exist.")

            except Exception as e:
                    speak("Sorry Sir, due to some reasons I was unable to delete this directory.")
                    print(e)

def hide_folder(folder):
    """Hides all files and folders inside a given folder, then opens the parent directory for confirmation."""
    try:
        # Enclose folder path in double quotes to handle spaces
        command = f'attrib +h +s "{folder}" /s /d'
        os.system(command)  # Execute the command

        speak("All the files in this folder are now hidden, Sir.")
        
        # Open the parent directory for visual confirmation
        parent_dir = Path(folder).parent
        os.startfile(str(parent_dir))
        speak(f"The parent directory has been opened for your confirmation.")

    except FileNotFoundError:
        speak("Sorry Sir, I couldn't find the folder at the specified location. Please double-check the path.")
    except Exception as e:
        speak("Apologies Sir. I encountered an error while processing the folder. Please try again later.")
        print(e)
            


def unhide_folder(folder):
    """Unhides all files and folders inside a given folder, then opens the parent directory for confirmation."""
    try:
        # Enclose folder path in double quotes to handle spaces
        command = f'attrib -h -s "{folder}" /s /d'
        os.system(command)  # Execute the command

        speak("All the files in this folder are now visible to everyone. Hope you have made this decision on your own. Peace.")

        # Open the parent directory for confirmation
        parent_dir = Path(folder).parent
        os.startfile(str(parent_dir))
        speak("The parent directory has been opened for your confirmation, Sir.")

    except FileNotFoundError:
        speak("Sorry Sir, not able to find the folder at your given location. Please try again.")
    except Exception as e:
        speak("Sorry Sir. Unable to read this file. Please try again after some time.")
        print(e)

    
        

def archieve_zip(source, destination,name):
            try:
                    zip_path = f"{destination}\\{name}"  # Ensure full path
                    shutil.make_archive(zip_path, 'zip', source)

                    speak(f"Directory archived successfully as {name}.zip")
                    os.startfile(destination)
            except Exception as e:
                    speak("Sorry Sir. Unable to archive this directory.Please try again later.")
                    print(e)

def extract_zip(zip_path, destination):
            try: 
                    shutil.unpack_archive(zip_path, destination)
                    os.startfile(destination)
                    speak("Zip file extracted successfully")
            except Exception as e:
                    speak("Sorry Sir. Unable to extract this zip file.Please try again later.")
                    print(e)

def create_folder(directory_path):
            try:
                    
                    os.makedirs(directory_path)
                    os.startfile(directory_path)
                    speak("Directory created successfully")
            except Exception as e:
                    speak("Sorry Sir. Unable to create this directory. Please try again later")
                    print(e)
            
def create_file(file_path):
            # Extract the file extension
                _, extension = os.path.splitext(file_path)
                VALID_EXTENSIONS = {".txt", ".csv", ".py", ".json", ".log"}  # Allowed extensions
                if extension.lower() not in VALID_EXTENSIONS:
                    speak("Invalid file extension! Please use .txt, .csv, .py, .json, or .log extensions and try again later.")
                else:
                    try:
                        parent_dir = os.path.dirname(file_path)

                        # Check if parent directory exists, if not, create it
                        if not os.path.exists(parent_dir):
                            os.makedirs(parent_dir)

                        # Create the file
                        with open(file_path, 'w') as file:
                            pass

                        os.startfile(parent_dir)
                        speak("File created successfully at your given location.")

                    except Exception as e:
                        speak("Sorry Sir. Unable to create this file. Please try again later.")
                        print(e)


def increase_volume(steps):
    """Increase system volume."""
    try:
        for _ in range(steps):
            pyautogui.press("volumeup")
            time.sleep(0.1)
    except Exception as e:
        speak("Unable to increase the systems volume. Please try again later.")

def decrease_volume(steps):
    """Decrease system volume."""
    try:
        for _ in range(steps):
            pyautogui.press("volumedown")
            time.sleep(0.1)
    except:
       speak("Unable to decrease the systems volume. Please try again later.")

def execute_system_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            output = result.stdout.strip()
            speak("Command executed successfully within our current working directory.")
            return output if output else "✅ Command executed successfully."
        else:
            speak("Error executing the command. Please check and try again.")
            return f"❌ Error: The command '{command}' failed.\n{result.stderr.strip()}"

    except Exception as e:
        speak("Sorry Sir. An error occurred while executing the command. Please try again later.")
        return f"❌ Exception: {str(e)}"

def mute_volume():
    """Mute/unmute system volume."""
    try:
        pyautogui.press("volumemute")
    except:
        speak("Not able to perfrom this Task. Please try again later")

def play_on_yt(topic):
    try:
        if not topic:
            speak("Sorry Sir, I did not catch that. Please provide a topic to play on YouTube.")
            return
        
        speak(f"Playing a video on {topic}")
        pywhatkit.playonyt(topic)
        speak(f"Opened YouTube and played a video on {topic} successfully.")
    
    except Exception as e:
        speak("Sorry Sir, due to some issue I was not able to play a video on YouTube.")
        print(f"JARVIS: Error playing video on YouTube: {e}")

               

def set_alarm(time):
            try:            
                            import MyAlarm_Module
                            MyAlarm_Module.start_alarm(time)  # Runs alarm in background
                     
            except Exception as e:
                        speak("Sorry Sir unable to set the alarm. Please check your alarm timing format and try again later.")

# Initialize global i
i = 1

def take_screenshot():
    global i
    try:
        speak("Sir, I am about to take the screenshot. Please finalize the screen you want to capture within few seconds.")
        time.sleep(4)

        while os.path.exists(f"jarvis_sc{i}.png"):
            i += 1  # Skip to next available number

        pic = pyautogui.screenshot()
        pic.save(f"jarvis_sc{i}.png")

        speak(f"I am done Sir, the screenshot has been saved as jarvis_sc{i}.png in the main folder.")
        i += 1  # Prepare for the next screenshot

    except Exception as e:
        speak("Sorry Sir, I was unable to take the screenshot.")
        print(e)

def weather(city):
                        speak(f"Please wait Sir. Fetching the weather of {city} city")
                        try:
                                    API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
                                    url_openWeather = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
                                    response = requests.get(url_openWeather)
                                    data = response.json()

                                    if data["cod"] == 200:
                                        temperature = data["main"]["temp"]
                                        condition = data["weather"][0]["description"]
                                        location = data["name"]

                                        speak(f"Sir, the current weather in {location} is {condition} with a temperature of {temperature}°C.")

                                    else:
                                        speak("Sorry Sir, I couldn't fetch the weather. Please say just the name of the city only and nothing else like-: Chennai , Mumbai etc.")

                        except Exception as e:
                                        speak("Sorry Sir, I couldn't fetch the weather due to some reasons. Please try again after few minutes")





def handle_how_to_query(query):
    speak(f"Ok Sir, Please wait for some time. I will tell you {query} in a detailed and structured format.")

    prompt = f"""
You are JARVIS, an intelligent assistant. Provide a detailed, structured, step-by-step guide in response to the following "how-to" task:

TASK: "{query}"

Your answer should include:
1. A short introduction explaining what the task is.
2. A list of required tools or materials (if applicable).
3. Numbered, step-by-step instructions (clearly written and easy to follow).
4. Any warnings, precautions, or common mistakes to avoid.
5. Optional tips or pro insights (only if relevant).

Format your answer like:
- Introduction:
- Requirements:
- Steps:
- Warnings:
- Tips:

Be clear, concise, and helpful. Keep it practical for everyday use.

Now generate the full guide but do not elaborate.
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # ✅ Save response to Word document
        doc = Document()
        doc.add_heading(f'How To Guide: {query}', level=1)
        doc.add_paragraph(response_text)

        filename = f"HowTo_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(os.getcwd(), filename)
        doc.save(filepath)

        speak("Sir, I have completed the guide and saved it as a Word document in our directory.")
        print(f"📄 Guide saved as: {filename}")

        return response_text

    except Exception as e:
        return "Sorry sir, I am unable to retrieve the steps at the moment."


def send_sms_message(context):
    try:
        if not context:
            speak("I did not catch the context. Please try again later.")
            return

        speak("Generating the message based on your context Sir.")

        prompt = f"Write a short, concise message for SMS. Context: {context}"
        try:
            response = model.generate_content(prompt)
            refined_msg = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")
            speak("Sorry Sir. Could not rephrase the message.Please try again later")
            return

        if not refined_msg:
            speak("Gemini did not return a valid message.")
            return

        speak("Please wait Sir, Sending message in a bit...")

        account_sid = os.getenv("ACCOUNT_SID")
        auth_token = os.getenv("AUTH_TOKEN")
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=refined_msg,
            from_="+12766885691",  # Your Twilio verified number
            to="+919324354021"     # Target number
        )

        speak("Message sent successfully to your number!")
        print(f"📩 SMS SID: {message.sid}\n📨 Message Sent: {refined_msg}")

    except Exception as e:
        speak("❌ Sorry Sir. Unable to send the message. Please try again later.")
        print(f"SMS Error: {e}")

def send_voice_call(context):
    try:
        if not context:
            speak("I did not catch the context. Please try again later.")
            return

        speak("Generating your voice message based on your context...")

        prompt = f"Write a short, clear message suitable for a voice call. Context: {context}"
        try:
            response = model.generate_content(prompt)
            refined_msg = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")
            speak("Sorry Sir. Could not rephrase the message.")
            return

        if not refined_msg:
            speak("Gemini did not return a valid voice message.")
            return

        speak("Please wait Sir, calling in a bit...")

        account_sid = os.getenv("ACCOUNT_SID")
        auth_token = os.getenv("AUTH_TOKEN")
        client = Client(account_sid, auth_token)

        voice_call = client.calls.create(
            twiml=f'<Response><Say>{refined_msg}</Say></Response>',
            from_="+12766885691",  # Your Twilio verified number
            to="+919324354021"     # Target number
        )

        speak("Successful voice call on your number.")
        print(f"📞 Voice Call SID: {voice_call.sid}\n🔊 Message Sent: {refined_msg}")

    except Exception as e:
        speak("❌ Sorry Sir. Unable to send the voice message. Please try again later.")
        print(f"Voice call error: {e}")


def is_notepad_open():
    """Check if Notepad is still running"""
    for process in psutil.process_iter(attrs=['name']):
        if "notepad" in process.info['name'].lower():
            return True
    return False

def open_google_search(query):
    try:
                            if not query:
                                speak("Sorry, I did not catch that. Please type what you would you like to search again")
                            else:
                                speak(f"Opening Google and Searching for {query}")
                                # Creating a Google search URL with the query
                                search_url = f"https://www.google.com/search?q={query}"
                                webbrowser.open(search_url)  # Opening the URL in the default browser
                                time.sleep(2)
                                speak(f"Succesfully opened google and Searched on {query}")
                                
    except Exception as e:
                        speak("Sorry Sir. Not able to open google. Please try again later")




local_tz = pytz.timezone("Asia/Kolkata")  # Set this to your time zone (IST)


SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_account():
    """Authenticate and create the Google Calendar API service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('Credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service


def format_time_to_am_pm(iso_time):
    """Converts ISO 8601 time format to 12-hour AM/PM format."""
    dt = datetime.fromisoformat(iso_time[:-6])  # Removing timezone info
    return dt.strftime("%I:%M %p")  # Example: "02:30 PM"


local_tz = pytz.timezone("Asia/Kolkata")  # Set this to your time zone (IST)


SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_account():
    """Authenticate and create the Google Calendar API service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('Credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service


def format_time_to_am_pm(iso_time):
    """Converts ISO 8601 time format to 12-hour AM/PM format."""
    dt = datetime.fromisoformat(iso_time[:-6])  # Removing timezone info
    return dt.strftime("%I:%M %p")  # Example: "02:30 PM"

def fetch_events_today():
    """Fetches events from Google Calendar for a specific date."""
    date = datetime.now().date()
    service = authenticate_google_account()
    time_min = f"{date}T00:00:00+05:30"
    time_max = f"{date}T23:59:59+05:30"

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            speak("There are no events scheduled for you today Sir. Let me know if you’d like me to check something else.")
            return
        else:
            speak("Today you have following events on your Schedule Sir")
            for event in events:
                summary = event.get('summary', '(No Title)')
                description = event.get('description', 'No description provided')
                start = event.get('start', {})
                end = event.get('end', {})

                if 'date' in start:  # All-day event
                   speak(f"- {summary} (All-day event)")
                elif 'dateTime' in start:
                    # Format the start and end time in HH:MM AM/PM format
                    start_time = format_time_to_am_pm(start['dateTime'])
                    end_time = format_time_to_am_pm(end['dateTime'])
                    speak(f"- {summary} from {start_time} to {end_time}")
                else:
                    speak(f"- {summary} (Unknown time format)")

                speak(f"  Description: {description}")
            return events  # Return events if needed

    except HttpError as error:
        speak(f"An error occurred while fetching events: {error}")

def fetch_events(date):
    """Fetches events from Google Calendar for a given date."""
    service = authenticate_google_account()
    time_min = f"{date}T00:00:00+05:30"
    time_max = f"{date}T23:59:59+05:30"

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            timeZone='Asia/Kolkata',  # 👈 This line ensures response is in IST
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return events  # Return events in IST for frontend

    except HttpError as error:
        return [f"An error occurred: {error}"]



def add_event(event_data):
    """Adds an event to Google Calendar."""
    date = event_data.get("date")
    event_summary = event_data.get("summary")
    event_description = event_data.get("description", "No description provided")
    start_time_input = event_data.get("start_time")
    start_am_pm = event_data.get("start_am_pm")
    end_time_input = event_data.get("end_time")
    end_am_pm = event_data.get("end_am_pm")

    # Handling all-day events
    if not start_time_input and not end_time_input:
        event = {
            'summary': event_summary,
            'description': event_description,
            'start': {'date': date},
            'end': {'date': date}
        }
    else:
        # Convert time to 24-hour format
        def convert_to_24hr(time_str, am_pm):
            hour, minute = map(int, time_str.split(":"))
            if am_pm.upper() == "PM" and hour != 12:
                hour += 12
            if am_pm.upper() == "AM" and hour == 12:
                hour = 0
            return f"{hour:02}:{minute:02}"

        start_time_24hr = convert_to_24hr(start_time_input, start_am_pm)
        end_time_24hr = convert_to_24hr(end_time_input, end_am_pm)

        event = {
            'summary': event_summary,
            'description': event_description,
            'start': {'dateTime': f"{date}T{start_time_24hr}:00+05:30", 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': f"{date}T{end_time_24hr}:00+05:30", 'timeZone': 'Asia/Kolkata'}
        }

    service = authenticate_google_account()
    try:
        speak("Please wait while I add the event to your schedule.")
        created_event = service.events().insert(calendarId='primary', body=event).execute()

        # Convert UTC datetime to IST
        def convert_to_ist(iso_str):
            utc_dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            ist = pytz.timezone("Asia/Kolkata")
            return utc_dt.astimezone(ist).strftime("%I:%M %p")  # Only time, 12-hour format


        event_start = created_event.get("start", {}).get("dateTime")
        event_end = created_event.get("end", {}).get("dateTime")

        if event_start and event_end:
            event_start_ist = convert_to_ist(event_start)
            event_end_ist = convert_to_ist(event_end)
        else:
            event_start_ist = event_end_ist = date

        response = f"Event successfully added:\n{event_summary}\n Date: {date}\nFrom {event_start_ist} to {event_end_ist}\n {event_description}"
        return response

    except HttpError as e:
        return f"❌ Unable to add event. An error occurred: {e}"

def delete_event_by_summary(date, summary=None, delete=False, fetch_only=False):
    """Fetches or deletes an event from Google Calendar."""
    service = authenticate_google_account()
    time_min = f"{date}T00:00:00+05:30"
    time_max = f"{date}T23:59:59+05:30"

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            return []

        if fetch_only:
            event_list = []
            for event in events:
                summary = event.get('summary', '(No Title)')
                start = event.get('start', {})
                if 'dateTime' in start:
                    start_time = format_time_to_am_pm(start['dateTime'])
                    event_list.append(f"{summary} - {start_time}")
                else:
                    event_list.append(f"{summary} (All-day event)")
            return event_list

        for event in events:
            if event['summary'].strip().lower() == summary.strip().lower():
                event_id = event['id']

                if delete:
                    service.events().delete(calendarId='primary', eventId=event_id).execute()
                    return f"Event '{summary}' on {date} has been deleted successfully."

        return f"❌ No event found with the name '{summary}' on {date}."

    except HttpError as error:
        return f"❌ An error occurred while fetching/deleting events: {error}"



def Task_Execution(query):
            query = query.lower()
    # greet()
    
        # Logic Building for tasks-:
            if "open notepad" in query:
                    speak("Opening Notepad")
                    os.system("start notepad")
                    time.sleep(2)
                    speak("Notepad Opened succesfully")
                    
                    

            elif "open command prompt" in query:
                speak("Opening command prompt")
                os.system("start cmd")
                time.sleep(1)
                speak("Opened command prompt succesfully")

    # DOUBT-: [Not able to use command-:"switch off the camera"]
            elif "webcam" in query:
                speak("Switching on the webcam")
                cap = cv2.VideoCapture(0)
                speak("Press escape to switch off the webcam")
                while True:
                    ret, img = cap.read()
                    cv2.imshow('webcam', img)
                    k = cv2.waitKey(50)
                    if k==27:
                        speak("Switching off the webcam")
                        break
                cap.release()
                cv2.destroyAllWindows()
                speak("webcam Switched off succesfully")

            # elif "play music"

            elif "ip add" in query:
                try:
                    ip = get('https://api.ipify.org').text
                    speak(f"Sir Your IP address is: {ip}")
                except Exception as e:
                    speak("Sorry Sir. Unable to get your Public IP address")


            

            elif "wikipedia" in query:
                speak("Type what you want to search on wikipedia")
                try: 
                        query = input()
                        wikipedia_search(query)
                except Exception as e:
                    speak("Sorry Sir not able to search on wikipedia. Try again after some time.")
                    print(e)
    
            elif "docs" in query:
                try:
                    speak("Opening Google Docs")
                    webbrowser.open("https://docs.google.com/document/u/1/")
                    time.sleep(2)
                    speak("Google Docs opened Succesfully")
                except:
                    speak("Sorry Sir. Not able to open Google docs")
                    print(e)

            # elif "open  chatgpt" in query:
            #     speak("Opening ChatGPT")
            #     webbrowser.open("chatgpt.com")




        # Function to handle opening Google with a search term
            elif "open google" in query:
                speak("Sir, what should I search on Google?")
                cm = input() # Taking the user's search term
                open_google_search(cm)
                


            elif "open whatsapp" in query:
                speak("Please type the recipient's phone number, including country code.")
                number = input()
                send_whatsapp(number)

            


            elif "open email" in query:
                try:
                    speak("Please type the recipient's email address: ")
                    to = input("Enter the recipient's email address: ")
                    sendEmail(to)
                except Exception as e:
                    print(e)
                    speak("Sorry Sir, unable to send this Email")



            elif "open youtube" in query:
                speak("Sir, What should i play on youtube")
                cm = input()
                play_on_yt(cm)
                
                        
         

            elif "window" in query:
                try:
                    speak("Switching window Sir")
                    pyautogui.keyDown("alt")
                    pyautogui.press("tab")
                    time.sleep(1)
                    pyautogui.keyUp("alt")
                    speak("Window Switched Succesfully")
                except Exception as e:
                    speak("Sorry Sir. Unable to switch the window")
                    print(e)

            # elif "news" in query:
            #     speak("Please wait Sir. Fetching the latest news")
            #     news()
 

            elif "set alarm" in query or "set an alarm" in query:
                speak("Sir, Please tell me the time to set the alarm, Time Format example:5:30 AM")
                set_alarm(time)
                

            elif "close notepad" in query or "close the notepad" in query:
                        speak("Ok sir, Closing Notepad")
                        os.system("taskkill /f /im notepad.exe")
                        speak("Notepad Closed succesfully")

            elif "close command prompt" in query or "close the command prompt" in query:
                        speak("Ok sir, Closing Command Prompt")
                        os.system("taskkill /f /im cmd.exe")
                        speak("Command Prompt Closed succesfully")

            elif "shutdown the system" in query:
                speak("Shutting down the system Sir.")
                os.system("shutdown /s /t 5") 

            elif "restart the system" in query:
                speak("Restarting the system Sir.")
                os.system("shutdown /r /t 5")
            
  
            elif "insta profile" in query or "instagram" in query:
                try:
                    speak("Sir Please enter the username correctly")
                    name = input("Enter the UserName here:")
                    webbrowser.open(f"www.instagram.com/{name}")
                    speak(f"Sir here is the profile of user {name}")
                    speak("Sir would you like to download the profile picture of this account? Say yes or no.")
                    while True:
                        condition = takeCommand()
                        if "yes" in condition:
                            mod = instaloader.Instaloader()
                            mod.download_profile(name, profile_pic_only=True)
                            speak("I am done sir. Profile Pic is saved in our Main Folder.")
                            break
                        elif "no" in condition:
                            break
                        else:
                            speak("Plase say either yes or no to download the profile picture of this account")
                except Exception as e:
                    speak("Sorry Sir. Unable to perform this task. Please try again after some time.")
                    print(e)

            elif "screenshot" in query:
                take_screenshot()

         
            
            elif "unhide folder" in query or "visible" in query:
                speak("Sir, please type the folder location whose all files you want to UNHIDE.")
                folder = input("Enter the folder address here: ").strip()
                unhide_folder(folder)

            elif "hide folder" in query:
                speak("Sir, please type the folder location whose all files you want to HIDE.")
                folder = input("Enter the folder address here: ").strip()
                hide_folder(folder)

   
            elif "weather" in query or "temperature" in query:
                speak("Please type the city name only to fetch it's weather")
                # while True:
                city = input()
                    # if not city:
                    #     speak("Sorry I did not catch that. Please say the city name to fetch it's weather")
                    # else:
                       
                speak(f"Please wait Sir, trying to fetch the weather of {city} city.")
                weather(city)
                

            elif "how to" in query:
                response = handle_how_to_query(query)
                speak(f"Here is the detailed answer on {query} which was saved in the document also. Please Read the entire instructions carefully")
                print(response)
                
            elif "network speed" in query or "system up time" in query or "system uptime" in query:
                    speak("Checking System's uptime and network speed information")
                    try:
                        # Get system uptime
                        uptime_seconds = time.time() - psutil.boot_time()
                        # uptime_delta = datetime.timedelta(seconds=int(uptime_seconds))  # Convert to timedelta
                        uptime_delta = timedelta(seconds=int(uptime_seconds))


                        hours = uptime_delta.seconds // 3600
                        minutes = (uptime_delta.seconds % 3600) // 60
                        seconds = uptime_delta.seconds % 60

                        uptime_message = f"{hours} hours, {minutes} minutes, and {seconds} seconds."

                        # Get network usage
                        net_io1 = psutil.net_io_counters()
                        time.sleep(1)  # Wait for 1 second to calculate speed
                        net_io2 = psutil.net_io_counters()
                        
                        bytes_sent = net_io2.bytes_sent
                        bytes_recv = net_io2.bytes_recv
                        upload_speed = (net_io2.bytes_sent - net_io1.bytes_sent)  # Bytes per second
                        download_speed = (net_io2.bytes_recv - net_io1.bytes_recv)  # Bytes per second
                        speak("Here are the results of system network speed test-:")
                        speak(f"System Uptime: {uptime_message}")
                        speak(f"Total Data Sent: {bytes_sent / (1024**2):.2f} MB, Total Data Received: {bytes_recv / (1024**2):.2f} MB")
                        speak(f"Current Upload Speed: {upload_speed / 1024:.2f} KB/s, Current Download Speed: {download_speed / 1024:.2f} KB/s")
                    except Exception as e:
                        speak("Sorry Sir. Unable to give you the system network speed test results. Please try again later.")
                        print(e)
                     

            elif "speed test" in query or "internet speed" in query:
                speak("Please wait for some time Sir to perform Speed test for our systems Internet. It might take more than a minute.")
# We divide by 1000000 (or 1_000_000 for readability) to convert the speed from bits per second (bps) to megabits per second (Mbps).
# st.download() and st.upload() return values in bits per second (bps).
# 1 Megabit (Mb) = 1000000 bits (or 10⁶ bits).
# To convert bits per second (bps) to Megabits per second (Mbps), we divide by 1,000,000.
                try:
                    st = speedtest.Speedtest()
                    # st.get_best_server()
                    download = st.download() / 1_000_000
                    upload = st.upload() / 1_000_000
                    ping = st.results.ping
                    result_url = st.results.share()  # Get a shareable image of results
                    speak("Here is your Internet Speed Stats-:")
                    stats = (
                                f"Downloading speed: {download:.2f} Mega bytes per second\n"
                                f"Uploading speed: {upload:.2f} Mega bytes per second\n"
                                f"Ping time: {ping} milliseconds"
                             )
                    speak(stats)
                    webbrowser.open(f"{result_url}")
                    time.sleep(2)
                    speak("I am displaying the image of speedtest done by okle")
                except Exception as e:
                    speak("Sorry Unable to perform speed test. It might be an issue due to our systems internet connection")



            elif "message" in query:
                speak("What message I have to send Sir?")
                msg = input()
                send_sms_message(msg)
                       
                '''
                            # Both numbers-: "from" and "to" should be verified by twilio

                            # So; you can seng message amd calls to those number with which
                            are VERIFIED by twilio. Your logged-in number is by-default verified by twilio.

                        # You can also add MORE verified numbers on twilio website MANUALLY
                 '''
                                                            
                        #✅ The message.sid confirms successful delivery.
                #     speak(f"Message sent successfully! to your Number")
                #     print(f"Message SID: {message.sid}")
                    
                # except Exception as e:
                #     speak("Sorry Sir. Unable to send the message. Please try again after some time")



            elif "call" in query:
       
                    speak("What voice message I have to send Sir?")
                       
                    msg = input()
                    send_voice_call(msg)   
                            
                    


                #                 voice_call = client.calls.create(
                # # this below format is necessary when using Twilio's Voice API to make automated calls. 
                # # This is Twilio Markup Language (TwiML), an XML-based format used to instruct Twilio on how to handle the call.
                #                     twiml = f'<Response><Say>{msg}</Say></Response>',
                # # <Response>: This is the root tag required in TwiML responses.
                # # <Say>: This tells Twilio to convert the text inside it into speech during the call.
                #                     from_ ="+12766885691",  # Your Twilio number
                #                     to="+919324354021"   # Receiver's number
                #                     )
                                
                #                 #✅ The voice_call.sid confirms successful delivery.
                #                 speak(f"Succesfull voice call on your number")
                #                 print(f"sID:{voice_call.sid}")
                #                 break
                # except Exception as e:
                #     speak("Sorry Sir. Unable to send the Voice message on your phone number. Please try again later.")

            elif "increase volume" in query or "increase the volume" in query:
                speak("Increasing Systems volume Sir.")
                increase_volume(10)
                time.sleep(1)
                speak("Increased Systems volume succesfully")

            elif "decrease volume" in query or "decrease the volume" in query:
                speak("Decreasing Systems volume Sir.")
                decrease_volume(10)
                time.sleep(1)
                speak("Decreased Systems volume succesfully")

            elif "unmute volume" in query or "unmute the volume" in query:
                speak("Unmuting Systems volume sir")
                mute_volume()
                time.sleep(1)
                speak("Succesfully Unmuted the Systems volume")
            
            elif "mute volume" in query or "mute the volume" in query:
                speak("muting Systems volume sir.")
                mute_volume()
                time.sleep(1)
                speak("Succesfully Muted the Systems volume")


           

# For this below query to run SUCCESFULLY-: You always need to connect your mobile-hotspot to your system-:
            elif "open mobile camera" in query or "open the mobile camera" in query:
                try:
                    speak("Opening Mobile Camera Sir.")
                    speak("Sir Please make sure that your laptops Wi-Fi is connected to your mobiles HotSpot then only I will be able to access your mobiles camera")
                    import urllib.request
                    import numpy as np
                    url = "http://192.168.160.247:8080/shot.jpg"
                    speak("Press q to switch off the mobile camera")
                    while True:
                        img_arr = np.array(bytearray(urllib.request.urlopen(url).read()),dtype=np.uint8)
                        img = cv2.imdecode(img_arr,-1)
                        cv2.imshow('IPWebcam',img)
                        q = cv2.waitKey(1)
                        if q == ord("q"):
                            break
                    cv2.destroyAllWindows()
                    speak("Succesfully closed the Mobile Camera")
                except Exception as e:
                    speak("Sorry Sir. Due to some reasons unable to access your mobile camera. Please try again after some time.")

            


            elif "basic system" in query:
                speak("Checking basic system info")
                try:
                    cpu_usage = psutil.cpu_percent(interval=1)
                    ram_usage = psutil.virtual_memory().percent
                    swap_memory_usage = psutil.swap_memory().percent
                    disk_usage = psutil.disk_usage('/').percent
                    battery = psutil.sensors_battery().percent

                # Will decide later on how to include the "NETWORK SECTION" in this basic system info section-:

                    speak("Here is your basic system info.")
                    speak(f"CPU Usage: {cpu_usage}%")
                    speak(f"RAM Usage: {ram_usage}%")
                    speak(f"Swap Memory Usage: {swap_memory_usage}%")
                    speak(f"Disk Usage: {disk_usage}%")
                    speak(f"Battery Percentage: {battery}%")
                except Exception as e:
                    speak("Sorry Sir. Unable to give you system stats. Please try again later.")
            
            elif  "cpu" in query:
                speak("Checking CPU Info")
                try:
                    cpu_usage = psutil.cpu_percent(interval=1)
                    cpu_count = psutil.cpu_count(logical=True)
                    physical_cores = psutil.cpu_count(logical=False)
                    cpu_freq = psutil.cpu_freq()
                    speak("Here is your CPU status.")
                    speak(f"CPU Usage: {cpu_usage}%")
                    speak(f"Total Logical Cores: {cpu_count}")
                    speak(f"Total Physical Cores: {physical_cores}")
                    speak(f"Current CPU Frequency: {cpu_freq.current:.2f} MHz")
                    speak(f"Maximum CPU Frequency: {cpu_freq.max:.2f} MHz")
                except Exception as e:
                    speak("Sorry Sir. Unable to give you CPU information. Please try again later.")

            elif "ram" in query:
                speak("Checking RAM info")
                try:
                    """ Get RAM information """
                    ram_info = psutil.virtual_memory()
                    ram_total = ram_info.total // (1024 ** 3)  # Convert bytes to GB
                    ram_available = ram_info.available // (1024 ** 3)
                    ram_used = ram_info.used // (1024 ** 3)
                    ram_percent = ram_info.percent
                    speak("Here is your RAM status.")
                    speak(f"Total RAM: {ram_total} GB")
                    speak(f"Available RAM: {ram_available} GB")
                    speak(f"Used RAM: {ram_used} GB")
                    speak(f"RAM Usage: {ram_percent}%")
                except Exception as e:
                    speak("Sorry Sir. Unable to give you RAM information. Please try again later.")

            elif "swap" in query:
                speak("Checking Swap Memory info")
                try:
                    """ Get Swap Memory information """
                    swap_info = psutil.swap_memory()
                    swap_total = swap_info.total // (1024 ** 3)
                    swap_used = swap_info.used // (1024 ** 3)
                    swap_free = swap_info.free // (1024 ** 3)
                    swap_percent = swap_info.percent
                    speak("Here is your Swap Memory status.")
                    speak(f"Total Swap Memory: {swap_total} GB")
                    speak(f"Used Swap Memory: {swap_used} GB")
                    speak(f"Free Swap Memory: {swap_free} GB")
                    speak(f"Swap Memory Usage: {swap_percent}%")
                except Exception as e:
                    speak("Sorry Sir. Unable to give you swap memory information. Please try again later.")

            elif "disk" in query:
                speak("Checking disk usage")
                try:
                    drive =  "C:\\"  # Windows C: drive
                    disk_usage = psutil.disk_usage(drive)
                    disk_total = disk_usage.total / (1024 ** 3)  # Convert to GB
                    disk_free = disk_usage.free / (1024 ** 3)    # Convert to GB
                    disk_used = disk_usage.used / (1024 ** 3)    # Convert to GB
                    disk_percentage = disk_usage.percent         # Percentage remains the same
                    disk_info = f"Drive: C Drive, Total Space: {disk_total:.2f} GB, Free Space: {disk_free:.2f} GB, Used Space: {disk_used:.2f} GB, Drive Usage: {disk_percentage}%"
                    speak(disk_info)
                except Exception as e:
                    speak("Sorry Sir. Unable to give you disk usage memory information. Please try again later.")


            elif "battery" in query or "power" in query:
                speak("Checking battery status")
                try:
                    psutil.sensors_battery()
                    battery = psutil.sensors_battery()
                    battery_percentage = battery.percent
                    battery_plugged = battery.power_plugged
                    battery_timeleft = battery.secsleft
                    if battery_timeleft == psutil.POWER_TIME_UNKNOWN:
                        battery_timeleft = "Calculating..."
                    elif battery_timeleft == psutil.POWER_TIME_UNLIMITED:
                        battery_timeleft = "Plugged in"
                    else:
                        battery_timeleft = f"{battery_timeleft // 3600} hours {battery_timeleft % 3600 // 60} minutes"
                    if not battery_plugged and battery_timeleft != "Plugged in":
                        if battery_timeleft == "Calculating...":
                            battery_info = f"Sir our System has: {battery_percentage}% battery which is not in Charging mode and not able to calculate the battery life"
                            speak(battery_info)
                        else:
                            battery_info = f"Sir our System has: {battery_percentage}% battery which is not in Charging mode and battery life will last for {battery_timeleft}"
                            speak(battery_info)
                    
                        if battery_percentage>=75:
                            speak("We have enough power to continue our work")
                        elif battery_percentage>=40 and battery_percentage<75:
                            speak("We should keep our system in charging mode")
                        elif battery_percentage>=15 and battery_percentage<40:
                            speak("We don't have enough power to work, please connect to charging")
                        else:
                            speak("We have very low power, please connect to charging. the system will shutdown very soon")
                    else:
                        battery_info = f"Sir our System has: {battery_percentage}% battery and in Charging mode"
                        speak(battery_info)
                        if battery_percentage>=75:
                            speak("We have enough power to continue our work")
                        elif battery_percentage>=40 and battery_percentage<75:
                            speak("We should not remove our system from charging mode")
                        elif battery_percentage>=15 and battery_percentage<40:
                            speak("We don't have enough power to work, please do not remove our system from charging mode")
                        else:
                            speak("We have very low power, please do not remove our system from charging mode. the system will shutdown very soon")
                except Exception as e:
                    speak("Sorry Sir, I am not able to get the battery status of our system")
                    print(e)

           

            

            elif "copy file" in query:
                speak("Copying file")
                speak("Please tell me the source file path along with the file's extension")
                source = input("Enter the source file path with it's extension: ")
                speak("Please tell me the destination file path")
                destination = input("Enter the destination file path: ")
                copy_file(source, destination)
                

            

            elif "copy directory" in query or "copy folder" in query:
                speak("Copying directory")
                speak("Please tell me the source directory path")
                source = input("Enter the source directory path: ")
                speak("Please tell me the destination directory path and the destination path should be NON-EXISTENT")
        # The destination path should not EXIST i.e. the directory/destination folder should not be present. It will be created automatically.
        # If the destination folder is already present, then it will throw an error.
                destination = input("Enter the destination directory path that DOES NOT EXISTS: ")
                copy_folder(source, destination)
                

            elif "move file" in query:
                speak("Moving file")
                speak("Please tell me the source file path along with the file's extension")
                source = input("Enter the source file path with its extension: ")
                speak("Please tell me the destination path")
                destination = input("Enter the destination path: ")
                move_file(source, destination)
                

            elif  "move directory" in query or "move folder" in query:
                speak("Moving directory")
                speak("Please tell me the source directory path that should be EXISTENT")
                source = input("Enter the source directory path: ")
                speak("Please tell me the destination path that should also be EXISTENT")
                destination = input("Enter the destination path: ")
                move_folder(source, destination)


            

            elif "delete file" in query or "delete a file" in query:
                speak("Deleting file")
                speak("Please tell me the file path along with its extension")
                file_path = input("Enter the file path along with its extension: ").strip()
                delete_file(file_path)
                

                    

            elif "delete directory" in query or "delete folder" in query or "delete a directory" in query or "delete a folder" in query:
                speak("Deleting directory")
                speak("Please tell me the directory path")
                directory_path = input("Enter the directory path: ").strip()
                delete_folder(directory_path)
                


            elif "archive" in query or "zip a folder" in query or "zip folder" in query:
                    speak("Archiving directory")
                    speak("Please tell me the source directory path")
                    source = input("Enter the source directory path: ")  
                    speak("Please tell me the destination directory path")
                    destination = input("Enter the destination directory path: ") 
                    archieve_zip(source, destination) 
                    
            
            elif "extract a zip" in query or "unzip" in query or "extract zip" in query:
                    speak("Extracting zip file")
                    speak("Please tell me the zip file path along with .zip extension")
                    zip_path = input("Enter the zip file path: ")
                    speak("Please tell me the destination directory path that can be NON-EXISTENT also")
                    destination = input("Enter the destination directory path: ")
                    extract_zip(zip_path, destination)
                

            elif  "clean temp" in query:
                speak("Cleaning temporary files. Please wait for some time.")
                try:
                    temp_path = os.path.expandvars(r"%TEMP%")  # Get the user's temp folder
                    if os.path.exists(temp_path):
                        # Delete only files inside the temp folder, not the folder itself
                        for file_name in os.listdir(temp_path):
                            file_path = os.path.join(temp_path, file_name)
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)  # Remove file or symlink
                                elif os.path.isdir(file_path):
                                    shutil.rmtree(file_path)  # Remove folder
                            except Exception as e:
                                print("Failed to delete this below path")
                                print(file_path)
                                print(e)
                                print("Continuing the process to delete the remaining temporary files and folders")

                        
                        # Open the temp folder for confirmation
                        os.startfile(temp_path)
                        speak("Due to some reasons few Temporary files were not DELETED.")
                        speak("But Remaining Temporary files deleted successfully from our system!")
                    else:
                        speak("No temporary files found.")

                except Exception as e:
                    speak("Sorry Sir. Unable to clean the temporary files and folders. Please try again later")
                    print(e)




            elif "create folder" in query or "create a folder" in query or "create directory" in query or "create a directory" in query:
                speak("Creating directory")
                speak("Please tell me the directory path along with the new folder name")
                directory_path = input("Enter the directory path along with the new folder name: ")
                create_folder(directory_path)
                
            elif "create file" in query or "create a file" in query:
                speak("Please enter the file path-:")
                file_path = input("Enter the file path along with its extension: ").strip()
                create_file(file_path)


            elif "run command" in query or "execute command" in query or "run a command" in query or "execute a command" in query:
                try:
                    speak("Please type the command to execute within our current working directory")
                    while True:
                        speak("Enter the valid command to execute")
                        command = input("Enter the command to execute: ")
                        if "rmdir /s" in command:
                            speak("Type only either 'Y' to delete the folder or 'N' to discard the command and NOT delete the folder")

                        # Execute the command and capture output & errors
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)

                        if result.returncode == 0:  # Command executed successfully
                            speak("Command executed successfully within our current working directory")
                            if result.stdout:
                                print(f"Command Output:\n{result.stdout}")
                            break
                        else:  # Command failed
                            speak("Error executing the command. Please check the command and try again.")
                            print(f"Error: The command '{command}' failed with exit status {result.returncode}.")
                            if result.stderr:
                                print(f"Error Details:\n{result.stderr}")

                except Exception as e:
                    speak("Sorry Sir.An error occurred while executing the command.Please try again later")
                    print(f"Exception: {e}")


            
 
      
         # the for-else and while-else constructs are unique to Python and are not commonly found in other programming languages.

            elif "increase brightness" in query or "increase systems brightness" in query:
                speak("Increasing System Brightness")
                try:
                    increase_brightness()
                except Exception as e:
                    speak("Sorry Sir. Unable to increase the systems Brightness. Please try again later.")
                    print(e)

            elif "decrease brightness" in query or "decrease systems brightness" in query:
                speak("Decreasing System Brightness")
                try:
                    decrease_brightness()
                except Exception as e:
                    speak("Sorry Sir. Unable to decrease the systems Brightness. Please try again later.")
                    print(e)

            elif "increase" in query or "decrease" in query or "higher" in query or "lower"in query or "reset" in query or  "initial" in query or "default" in query:
                adjust_speech_rate(query)

            elif "systems speech" in query or "value of speech" in query:
                try:
                    speak(f"Sir, the current systems speech rate value is {speech_rate} words per minute.")
                except Exception as e:
                    speak("Sorry Sir Unable to get the current value of Systems speech rate. Please try after some time.")

            

            elif "today" in query:
                 fetch_events_today() 
            

            elif "image" in query or "picture" in query or "photo" in query:
                speak("Please enter the full file path of image")
                image_ = input("Enter the full file path along with the extension of image: ")
                speak("On what basis do i have to analyze this image?")
                desc_ = input("Enter the description here:")
                response = send_to_Gemini(desc_, image_path=image_)
                speak(response)

            elif is_real_time_query(query):
                speak("Fetching the latest real-time information, Sir.")
                try:
                    serp_data = search_serp_api(query)  # Get real-time data
                    
                    # ✅ Send real-time data to Gemini for natural rephrasing
                    response = send_to_Gemini(serp_data=serp_data)
                    
                    speak(response)  # Speak the corrected response
                except Exception as e:
                    speak("Sorry Sir, I couldn't fetch real-time results. Let me check another source.")
                    print(e)



            else:
                # speak("Let me check that for you.")
                response = send_to_Gemini(query)  # Get Gemini's response
                speak(response)  # Speak the