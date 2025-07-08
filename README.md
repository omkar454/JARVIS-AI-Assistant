
# 🔊 JARVIS: Personal Voice Assistant

> A Python-based intelligent desktop assistant powered by CustomTkinter GUI, Generative AI, system automation, and smart task execution.

---

## 👨‍💻 Project Contributors

This project was developed as a **Second Year Engineering (S.E.) Mini Project** by the following team members:

- **Rishi Notani** – [`@Rishinotani99`](https://github.com/Rishinotani99)  
- **Suhani Poptani** – [`@suhanip152`](https://github.com/suhanip152)  
- **Sonal Sharma** – [`@sonal120sharma`](https://github.com/Sonal-Sharma28)  
- **Omkar Raut** – [`@omkar454`](https://github.com/omkar454)

---

## 📌 About the Project

**JARVIS** is a personal AI-powered assistant built using Python and CustomTkinter. It performs intelligent automation tasks such as:

- Sending Emails, WhatsApp messages, SMS, and making voice calls
- Answering real-time and general queries using the **SERP API** and **Gemini API**
- Managing events using **Google Calendar API**
- Generating AI content (DOCX, notes, assignments, code, images, and YouTube summaries)
- Executing system-level operations (screenshots, folder management, shutdown, brightness, volume, webcam)
- Providing dynamic hardware info (CPU, RAM, disk, battery, internet speed)
- Maintaining an interactive GUI with command prompt, history, system log, and live stats

---

## ⚙️ Technologies Used

- **Python 3**
- **CustomTkinter** – For modern GUI design
- **Google Calendar API**
- **Google Gemini API** – For text/image-based generative tasks
- **SERP API** – For real-time query answering
- **Twilio API** – For SMS and call functionality
- **Other Libraries** – `pyttsx3`, `speech_recognition`, `pyautogui`, `psutil`, `cv2`, `shutil`, `PyPDF2`, etc.

---

## 📁 File Structure & Flow

### 🔹 `intro.py` – The Loading Screen

This file displays a futuristic loading screen with a progress bar, live system info, and boot logs.

![Loading Screen](C:\Users\Omkar Raut\OneDrive\Desktop\PYTHON\loading_screen.png)

➡️ After progress is complete, the program transitions to:

---

### 🔹 `jarvis_frontend1.py` – Main Prompt Interface

This is the main frontend GUI where users interact with JARVIS via text prompts. It includes:

- Left Panel: Chat History  
- Center Panel: Display Area  
- Bottom: Command Input + Hardware Info (CPU, RAM, Disk, Battery)  
- Top: Real-Time Clock  
- Voice and Text response system  
- Fade-out effect on `goodbye` command

![Main GUI](C:\Users\Omkar Raut\OneDrive\Desktop\PYTHON\main_screen.png)

---

### 🔹 `MainJarvis_Taskexecution.py` – Core Functionalities Engine

This file contains the **main logic** and core function calls of JARVIS. It is imported into `jarvis_frontend1.py` and does not have a GUI.

---

### 🔹 Other Modular Functional Files

These files handle **complex, individual tasks** and are all imported into `jarvis_frontend1.py`:

- `Assignment_Creation.py` – AI-based assignment generator
- `Code_debugged.py` – Multi-language code debugger
- `Medical_Analysis.py` – Health diagnostics via medical images
- `MyAlarm_Module.py` – Alarm setter
- `Official_Document_Extractor.py` – Document info extractor (Aadhar, invoice, etc.)
- `code_segment.py` – AI code generator
- `document_summarizer.py` – PDF and DOCX summarizer
- `food_nutritionist.py` – Meal photo analysis for nutrition
- `image_gen.py` – AI image generation
- `jarvis_data_analysis.py` – Data analysis + chart reporting from CSV
- `jarvis_docx_creator.py` – Word document/note generator
- `youtube_video_summarizer.py` – YouTube video transcript summarizer
- `jarvis_ppt.py` – **📌 Work in Progress (PPT generation)**  
  > *Module developed but not yet integrated into the main frontend; code committed to GitHub.*

### 🔸 `alarm.wav` – Sound file used as a ring tone when alarms are triggered (not a script).

---

## 💬 Interaction Format

> Type a command → JARVIS performs the task → Responds via **Text + Voice**

**Examples:**
- `open email` → opens default email client  
- `assignment on AI` → generates content using Gemini  
- `data analysis` → analyzes CSV and outputs report  
- `how to crack NDA` → gets info via SERP  
- `generate word` → creates formatted DOCX  
- `youtube` or `video` → plays/summarizes video  
- `alarm` → sets an alarm  
- `screenshot`, `webcam`, `shutdown` → system commands

---

## ✅ Completed vs In Progress

| Module                      | Status       |
| Module                     | Status       |
|----------------------------|--------------|
| Email, WhatsApp, Calendar  | ✅ Completed |
| File/folder management     | ✅ Completed |
| Code generation/debugging  | ✅ Completed |
| DOCX, assignment creation  | ✅ Completed |
| AI image & nutrition tools | ✅ Completed |
| Data analysis, summaries   | ✅ Completed |
| PPT generation             | 🔧 Work In Progress (code complete, GUI integration pending) |

---

## 🚀 How to Run the Project

### Requirements:
- Python 3.x
- Recommended: Create a virtual environment

### Install Dependencies:
```bash
pip install -r requirements.txt
```

### Run the Project:

```bash
python intro.py
```
➡️ The loading screen will appear.  
➡️ Then, the GUI (`jarvis_frontend1.py`) will launch automatically.
➡️ Then GUI (`jarvis_frontend1.py`) will launch automatically

---

## 📌 Future Enhancements

* 💬 **NLP Integration** for natural conversation
* 🌐 **Web/Mobile Support** for cross-platform use
* 🧠 **Advanced Gen-AI Content** (slides, diagrams, design)
* 🔄 **Scalable API Usage** with token management
* 🎙️ Optional **Voice Input** in addition to prompt typing

---

## 🔗 References

1. [JARVIS Full Implementation Guide – Avi Upadhyay](https://www.youtube.com/playlist?list=PLq_SHLFD-pSD_LeiV2dyAHgED7PDF48Jq)
2. [Gemini API Integration – Apna College](https://www.youtube.com/watch?v=mEsleV16qdo)
3. [Google Gemini Uses – Krish Naik](https://www.youtube.com/playlist?list=PLZoTAELRMXVNbDmGZlcgCA3a8mRQp5axb)
4. [ChatGPT – OpenAI](https://chat.openai.com)
5. [Gemini API – Google DeepMind](https://deepmind.google/technologies/gemini/)

---

## 🙏 Acknowledgments

We sincerely thank **Prof. Reshma Malik** for guidance and support throughout the project.
We also acknowledge the open-source community and tools like Gemini, ChatGPT, and the YouTube creators who made this learning journey possible.

---

## 📎 GitHub Repository

🔗 [JARVIS-AI-Assistant](https://github.com/omkar454/JARVIS-AI-Assistant)

---
```
