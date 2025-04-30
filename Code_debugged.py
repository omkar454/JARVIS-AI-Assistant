import os
import re
import subprocess
from datetime import datetime
from MainJarvis_TaskExecution import speak
import google.generativeai as genai



# Mapping language names to file extensions and comment styles
LANG_EXT_MAP = {
    "python": (".py", "#"),
    "javascript": (".js", "//"),
    "java": (".java", "//"),
    "c++": (".cpp", "//"),
    "c": (".c", "//"),
    "html": (".html", "<!-- -->"),
    "css": (".css", "/* */"),
    "bash": (".sh", "#"),
    "ruby": (".rb", "#"),
    "go": (".go", "//"),
    "php": (".php", "//"),
}

def get_code_input():
    print("\n📥 Paste your code below. Type 'END' (in uppercase) on a new line to finish:\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def debug_code(user_code, lang_hint="python"):
        # Configure your Gemini API key
    genai.configure(api_key=os.getenv("GEMINI_API_1"))
    model = genai.GenerativeModel("gemini-1.5-pro")
    """Analyzes and fixes code errors in any language and opens it in VS Code."""

    speak("Analyzing the code for debugging, sir.")
    print(f"[DEBUG] Language Hint Provided: {lang_hint}")

    prompt = f"""
You are an AI debugger. Analyze the following code, fix any issues, and explain the changes.
If the code is already correct, improve it and explain your enhancement.
Reply in plain text only with this structure:

Corrected Code:
[Corrected code here]

Explanation:
- [Bullet point explanations]

Input Code:
{user_code}
"""

    response = model.generate_content(prompt)

    if not response or not response.text:
        speak("Sorry sir, I couldn't debug the code. Please try again later.")
        return "Failed to debug code."

    output = response.text.strip()

    # Extract code and explanation
    code_match = re.search(r"Corrected Code:\s*(.*?)\s*Explanation:", output, re.DOTALL)
    explanation_match = re.search(r"Explanation:\s*(.*)", output, re.DOTALL)

    if not code_match or not explanation_match:
        speak("Couldn't parse the response properly, sir.")
        return "Failed to debug code."

    corrected_code = code_match.group(1).strip()
    explanation = explanation_match.group(1).strip()

    # Sanitize and validate language
    lang = lang_hint.strip().lower()
    if lang not in LANG_EXT_MAP:
        speak(f"Language '{lang}' not recognized, using default .txt extension.")
        ext, comment = ".txt", "#"
    else:
        ext, comment = LANG_EXT_MAP[lang]

    # Format explanation into comments
    if comment == "<!-- -->":
        comment_block = f"<!--\n{explanation}\n-->"
    elif comment == "/* */":
        comment_block = f"/*\n{explanation}\n*/"
    else:
        comment_block = "\n".join([f"{comment} {line}" for line in explanation.splitlines()])

    # Combine final output
    full_code = corrected_code + "\n\n" + comment_block
    filename = f"debugged_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    filepath = os.path.join(os.getcwd(), filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_code)
        speak("Code debugged successfully and saved in our current working directory.")
        print(f"✅ Code saved successfully as: {filename}")
        print(f"[INFO] File saved at: {filepath}")
    except Exception as e:
        speak("Sorry Sir. Error saving code to file. Please try again later.")
        print(f"[ERROR] {e}")
        return

    return f"✅ Code debugged and saved as: {filename}"

# 🔁 Main user interaction
if __name__ == "__main__":
    print("📌 Supported Languages:", ", ".join(LANG_EXT_MAP.keys()))
    lang = input("🔧 Enter the programming language of your code: ").strip().lower()

    if lang not in LANG_EXT_MAP:
        print(f"⚠️ Warning: Language '{lang}' not officially supported. Defaulting to .txt")

    user_code = get_code_input()
    result = debug_code(user_code, lang)

    if result:
        print(result)
