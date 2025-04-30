import os
import subprocess
import google.generativeai as genai
import sys
import re
from MainJarvis_TaskExecution import speak

# Configure Gemini API




# Supported languages and file extensions
language_extensions = {
    "python": "py",
    "java": "java",
    "c++": "cpp",
    "c": "c",
    "javascript": "js",
    "html": "html",
    "css": "css",
    "typescript": "ts",
    "go": "go",
    "php": "php",
    "ruby": "rb",
    "swift": "swift",
    "kotlin": "kt",
    "rust": "rs"
}

# Prompts by skill level
prompt_levels = {
    "beginner": """
Generate a beginner-friendly {language} program.
Include clear comments explaining each part.
Focus on readability and simplicity.
Task: {task}

Provide ONLY the code, formatted within a markdown code block like:
```{language}
""",
    "intermediate": """
Generate an intermediate-level {language} program.
Follow common best practices and coding conventions for {language}.
Include appropriate comments or basic documentation.
Task: {task}

Provide ONLY the code, formatted within a markdown code block like:
```{language}
""",
    "advanced": """
Generate a high-quality, complete, and optimized {language} program.
Include modular design, error handling, and relevant documentation (like docstrings/comments).
Consider efficiency and maintainability for complex tasks.
Task: {task}

Provide ONLY the code, formatted within a markdown code block like:
```{language}
"""
}

# Extract code from markdown
def extract_code_from_markdown(text, language):
    pattern = rf"```{re.escape(language)}\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        pattern_any = r"```\n(.*?)\n```"
        match_any = re.search(pattern_any, text, re.DOTALL)
        if match_any:
            print(f"Warning: Could not find a markdown block specifically for '{language}'. Extracting content from a generic ``` block.")
            return match_any.group(1).strip()
        else:
            print("Could not find any markdown code block (```) in the response.")
            return None

# print("🔧 AI Code Generator using Gemini\n")

# Get user input




def code_generate(prompt, language, level):
    try:
       genai.configure(api_key=os.getenv("GEMINI_API_1"))
       model = genai.GenerativeModel("gemini-1.5-pro")
    # model.generate_content("Ping", request_options={"timeout": 10})
    except Exception as e:
       print(f"Failed to connect to Gemini API or load model. Check your API key and network connection: {e}")
    # exit(1)
    if not prompt:
        print("Task description cannot be empty.")
        # exit()
    if language not in language_extensions:
        print(f"Unsupported language '{language}'. Supported languages: {', '.join(language_extensions.keys())}")
        # exit()
    if level not in prompt_levels:
        print(f"Invalid skill level '{level}'. Supported levels: {', '.join(prompt_levels.keys())}")
        # exit()

    # Filename generation
    file_ext = language_extensions[language]
    safe_prompt_snippet = "".join(c for c in prompt[:30].splitlines()[0] if c.isalnum() or c in (' ', '')).strip().replace(' ', '')
    if not safe_prompt_snippet:
        safe_prompt_snippet = "task"
    filename = f"generated_code_{safe_prompt_snippet}_{language}.{file_ext}"

    # Prepare full prompt for Gemini
    full_prompt = prompt_levels[level].format(language=language, task=prompt)
# Generate and save code
    try:
        speak(f"Generating code on {prompt}")
        response = model.generate_content(full_prompt, request_options={"timeout": 60})
        raw_response_text = response.text.strip()

        code = extract_code_from_markdown(raw_response_text, language)

        if not code:
            print("Failed to extract code from Gemini's response.")
            exit()

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
                speak("Code generated successfully and saved in our current working directory")
            print(f"Code saved successfully as: {filename}")
        except Exception as e:
            speak("Sorry Sir.Error saving code to file. Please try again later.")
            print(f"{e}")
            exit()

        
    except Exception as e:
        speak("Sorry Sir.Error saving code to file. Please try again later.")
        print(f"{e}")

if __name__ == "__main__":
    # Get user input for task, language, and skill level
    task = input("Enter the task description: ").strip()
    language = input(f"Enter the programming language ({', '.join(language_extensions.keys())}): ").strip().lower()
    level = input(f"Enter your skill level ({', '.join(prompt_levels.keys())}): ").strip().lower()

    code_generate(task, language, level)