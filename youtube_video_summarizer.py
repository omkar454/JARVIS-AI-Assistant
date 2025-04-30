from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from docx import Document
from datetime import datetime
import os
from MainJarvis_TaskExecution import speak
import google.generativeai as genai



def extract_video_id(youtube_url):
    parsed_url = urlparse(youtube_url)
    if "youtube.com" in parsed_url.netloc:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip("/")
    return None

def extract_transcript_details(youtube_url):
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return "❌ Invalid YouTube link. Please enter a valid URL.", None

        try:
            transcript_text = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
            language = "Hindi"
        except:
            transcript_text = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            language = "English"

        transcript = " ".join(i["text"] for i in transcript_text)
        return transcript, language

    except TranscriptsDisabled:
        return "❌ No subtitles available for this video.", None
    except Exception as e:
        return f"❌ Error fetching transcript: {e}", None

def generate_gemini_summary(transcript_text, language):
    # Gemini Configuration
    genai.configure(api_key= os.getenv("GEMINI_API_2"))  # Replace with your actual key
    model = genai.GenerativeModel("gemini-1.5-pro")
    hindi_prompt = """
आप एक AI-पावर्ड YouTube वीडियो संक्षेपणकर्ता हैं। आपका कार्य दिए गए ट्रांसक्रिप्ट का विश्लेषण करना और वीडियो की मुख्य जानकारी को संक्षिप्त बुलेट पॉइंट्स में प्रस्तुत करना है।

निर्देश:
- केवल मुख्य विषय और आवश्यक जानकारी शामिल करें।
- 200 शब्दों के भीतर संक्षेप रखें।
- कोई Markdown प्रतीक (जैसे *, #, आदि) का उपयोग न करें।
- प्रत्येक बुलेट पॉइंट के बीच एक खाली पंक्ति होनी चाहिए।

ट्रांसक्रिप्ट:
"""

    english_prompt = """
You are an AI-powered YouTube video summarizer. Your job is to analyze the following transcript and generate a clear and concise summary in bullet points.

Instructions:
- Focus only on key topics and major insights.
- Keep the summary under 250 words.
- Do NOT use Markdown symbols (*, #, etc.).
- Leave a blank line between each bullet point.

Transcript:
"""

    prompt = hindi_prompt if language == "Hindi" else english_prompt
    response = model.generate_content(prompt + transcript_text)
    return response.text.strip()

def summarize_youtube_video(youtube_url):

    speak("Fetching transcript from the YouTube video sir.")
    transcript_text, language = extract_transcript_details(youtube_url)

    if transcript_text and "❌" not in transcript_text:
        speak(f"Generating summary in {language}.")
        summary = generate_gemini_summary(transcript_text, language)

        # Word Document Setup
        doc = Document()
        doc.add_heading("🎥 YouTube Video Summary", 0)
        doc.add_paragraph("")
        doc.add_paragraph(f"🔗 Video Link: {youtube_url}")
        doc.add_paragraph(f"🕒 Summary Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph(f"📌 Language Detected: {language}")
        doc.add_paragraph("")

        doc.add_heading("📄 Structured Summary", level=1)
        doc.add_paragraph("")

        # Split summary into bullet points
        for bullet in summary.split("\n\n"):
            if bullet.strip():
                doc.add_paragraph(bullet.strip(), style='List Bullet')
                doc.add_paragraph("")  # Add spacing after each point

        # Save document
        filename = f"YouTube_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        path = os.path.join(os.getcwd(), filename)
        doc.save(path)

        speak("The YouTube video summary report is created and saved in our directory.")
        speak("Opening the file for you sir.")
        os.startfile(path)
        speak("File opened successfully.")
        return summary
    else:
        speak("Unable to fetch subtitles or transcript for this video.")
        return transcript_text
