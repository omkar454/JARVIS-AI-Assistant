import fitz  # PyMuPDF
import os
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import io
from datetime import datetime
import subprocess
import sys
from docx.shared import RGBColor
import re
from MainJarvis_TaskExecution import speak

# ====== Configure Gemini ======
# It's recommended to use environment variables for keys if possible
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_2") # Replace with your Gemini API Key

if GEMINI_API_KEY is None or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("❌ GEMINI_API_KEY not set. Please set it in the script or as an environment variable.")
    exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")
    # Simple test to check if the API key works and model is accessible
    # model.generate_content("Ping", request_options={"timeout": 10})
except Exception as e:
    print(f"❌ Failed to connect to Gemini API or load model. Check your API key and network connection: {e}")
    exit(1)


# ====== Text Chunking Function ======
# Adjusted max_chars slightly, consider the model's token limit including prompt/response
def chunk_text_smart(text, max_chars=7000):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    for i, paragraph in enumerate(paragraphs):
        # Estimate space needed for the paragraph plus separator
        space_needed = len(paragraph) + (2 if current_chunk else 0) # Add 2 for the potential \n\n before

        if len(current_chunk) + space_needed <= max_chars:
            current_chunk += ( "\n\n" if current_chunk else "") + paragraph
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # print(f"🧩 Total chunks created: {len(chunks)}")
    return chunks

# ====== Extract Text from PDF ======
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            # Use get_text("text") for basic text with block separation
            text += page.get_text("text") + "\n---\n" # Add separator between pages
        doc.close()
        # print("✅ Text extracted from PDF.")
        return text
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""

# ====== Extract Text from DOCX ======
def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n\n"
        # print("✅ Text extracted from DOCX.")
        return text
    except Exception as e:
        print(f"❌ Error reading DOCX: {e}")
        return ""

# ====== Helper function to add formatted paragraphs with Times New Roman and specified style/size ======
def add_styled_paragraph(doc, text, style='Normal', size_pt=Pt(12), bold=False, italic=False, color=None):
    p = doc.add_paragraph(text, style=style)
    for run in p.runs:
        font = run.font
        font.name = 'Times New Roman'
        font.size = size_pt
        run.bold = bold
        run.italic = italic
        if color:
            font.color.rgb = RGBColor(*color)


# ====== Markdown Parsing and Adding to Docx ======
def add_markdown_to_docx(doc, markdown_text, base_style='Normal', base_size_pt=Pt(11)):
    """
    Parses simple markdown from text and adds it to the docx document.
    Handles headings (#, ##, ###), lists (*, -), and bold (**).
    """
    lines = markdown_text.split('\n')
    list_style = 'List Bullet' # Use Word's List Bullet style
    current_list_paragraph = None # Track the current list item paragraph

    for line in lines:
        line = line.strip()

        if not line:
            # Add a blank line to separate paragraphs if needed (except within lists)
            if current_list_paragraph is None:
                 doc.add_paragraph('', style=base_style)
            continue # Skip empty lines

        # --- Check for Headings ---
        if line.startswith('### '):
            add_styled_paragraph(doc, line[4:].strip(), style='Heading 3', size_pt=Pt(12), bold=True) # Use Heading 3 style
            current_list_paragraph = None # Reset list tracking
        elif line.startswith('## '):
            add_styled_paragraph(doc, line[3:].strip(), style='Heading 2', size_pt=Pt(14), bold=True) # Use Heading 2 style
            current_list_paragraph = None # Reset list tracking
        elif line.startswith('# '):
            add_styled_paragraph(doc, line[2:].strip(), style='Heading 1', size_pt=Pt(16), bold=True) # Use Heading 1 style
            current_list_paragraph = None # Reset list tracking

        # --- Check for List Items ---
        elif line.startswith('* ') or line.startswith('- '):
            item_text = line[2:].strip()
            p = doc.add_paragraph(style=list_style) # Use the list style
            run = p.add_run() # Add a run to apply formatting

            # Apply bold formatting within the list item
            parts = re.split(r'(\*\*.*?\*\*)', item_text)
            for part in parts:
                run = p.add_run() # Add a run for each part
                if part.startswith('**') and part.endswith('**'):
                    run.text = part[2:-2] # Remove asterisks
                    run.bold = True
                else:
                    run.text = part
                run.font.name = 'Times New Roman' # Apply font
                run.font.size = base_size_pt # Apply base size to list items

            current_list_paragraph = p # Keep track of being inside a list

        # --- Handle Regular Paragraphs with Bold ---
        else:
            p = doc.add_paragraph(style=base_style) # Use the base style for regular text
            run = p.add_run() # Add a run to apply formatting

            # Apply bold formatting to regular text
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                run = p.add_run() # Add a run for each part
                if part.startswith('**') and part.endswith('**'):
                    run.text = part[2:-2] # Remove asterisks
                    run.bold = True
                else:
                    run.text = part
                run.font.name = 'Times New Roman' # Apply font
                run.font.size = base_size_pt # Apply base size to regular text

            current_list_paragraph = None # Reset list tracking


# ====== Create Word Summary Report ======
def save_summary_to_docx(synthesized_summary, chunk_summaries, output_path, document_title, document_topic, original_file_path):
    doc = Document()
    # Ensure 'Normal' style font is Times New Roman - this is a good base
    styles = doc.styles
    style_normal = styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Set font for Heading styles for consistency (optional, but helps)
    for style_name in ['Heading 1', 'Heading 2', 'Heading 3', 'Title', 'Subtitle']:
        try:
            style = styles[style_name]
            font = style.font
            font.name = 'Times New Roman'
        except KeyError:
            pass # Style might not exist in the default template


    # --- Add Title Page Elements ---
    add_styled_paragraph(doc, "Document Summary Report", style='Title', size_pt=Pt(36), bold=True, color=(0, 0, 0))
    add_styled_paragraph(doc, f"Document Title: {document_title}", style='Subtitle', size_pt=Pt(18), color=(0, 0, 0))
    add_styled_paragraph(doc, f"Topic: {document_topic}", style='Subtitle', size_pt=Pt(16), color=(0, 0, 0))
    add_styled_paragraph(doc, f"Original File: {os.path.basename(original_file_path)}", style='Subtitle', size_pt=Pt(12), color=(0, 0, 0))
    add_styled_paragraph(doc, f"Generated by JARVIS on {datetime.now().strftime('%Y-%m-%d %H:%M')}", style='Subtitle', size_pt=Pt(12), color=(0, 0, 0))
    doc.add_page_break()

    # --- Add Synthesized Summary ---
    add_styled_paragraph(doc, "Overall Document Summary", style='Heading 1', size_pt=Pt(18))
    if synthesized_summary:
        # Use the markdown helper for the main summary content
        add_markdown_to_docx(doc, synthesized_summary, base_size_pt=Pt(11))
    else:
        add_styled_paragraph(doc, "Could not generate an overall synthesis summary.", size_pt=Pt(11), italic=True, color=(255, 0, 0))


    # --- Add Individual Chunk Summaries (Optional / for detail) ---
    if chunk_summaries and len(chunk_summaries) > 0:
        doc.add_page_break() # Start on new page
        add_styled_paragraph(doc, "Detailed Chunk Summaries", style='Heading 1', size_pt=Pt(18))

        for i, summary in enumerate(chunk_summaries):
            add_styled_paragraph(doc, f"Chunk {i + 1}", style='Heading 2', size_pt=Pt(14))
            # Use the markdown helper for each chunk summary
            add_markdown_to_docx(doc, summary, base_size_pt=Pt(11))

    doc.save(output_path)
    print(f"Summary report saved as: {output_path}")
    return output_path

# ====== Summarization Prompt Generator (for individual chunks) ======
def generate_chunk_prompt(chunk, topic, purpose, audience, style="detailed and comprehensive"):
    return f"""
You are JARVIS, an expert summarization assistant. Your task is to provide a {style} summary of the following document chunk.

Include all key points and main ideas. Use markdown for structure:
-   Use `##` for main sections within the chunk summary.
-   Use `* ` or `- ` for bullet points.
-   Use `**text**` for bold text.

📘 DOCUMENT TOPIC: {topic}
🎯 PURPOSE OF SUMMARY: {purpose}
👥 TARGET AUDIENCE: {audience}

📄 DOCUMENT CHUNK:
\"\"\"{chunk}\"\"\"

🧠 INSTRUCTIONS:
- Provide a detailed and comprehensive summary of THIS CHUNK ONLY.
- Structure the summary using markdown headings and bullet points.
- Ensure the summary is accurate and reflects the chunk content.
- Maintain a professional and informative tone.
- Do NOT include information from other chunks.
- Start your response directly with the markdown summary.
"""

# ====== Synthesis Prompt Generator (for overall summary) ======
def generate_synthesis_prompt(chunk_summaries, document_title, document_topic, purpose, audience):
    summaries_text = "\n\n---\n\n".join(chunk_summaries) # Use a clear separator
    return f"""
You are JARVIS, an expert summarization assistant. Your task is to synthesize multiple individual chunk summaries into one cohesive overall summary of the entire document.

🔍 TASK: Synthesize the following chunk summaries into a single, professional, overarching summary.

Use markdown for structure in the final summary:
-   Use `##` for main sections/themes of the overall summary.
-   Use `* ` or `- ` for bullet points within sections.
-   Use `**text**` for bold text for emphasis.

📄 DOCUMENT TITLE: {document_title}
📘 DOCUMENT TOPIC: {document_topic}
🎯 PURPOSE OF SUMMARY: {purpose}
👥 TARGET AUDIENCE: {audience}

📝 INDIVIDUAL CHUNK SUMMARIES:
\"\"\"{summaries_text}\"\"\"

🧠 INSTRUCTIONS:
- Create a single, professional, and cohesive summary that covers the main ideas and key findings from all the chunk summaries.
- Structure the overall summary logically using markdown headings and bullet points.
- Focus on the most important information relevant to the document's topic and the target audience/purpose.
- The overall summary should be comprehensive but avoid getting lost in minor details already covered in chunk summaries.
- Ensure a smooth flow between points that originated from different parts of the original document.
- Conclude with the main takeaways or overall significance of the document's content.
- Maintain a professional and authoritative tone.
- Start your response directly with the markdown summary.
"""

# ====== Get Summary from Gemini (Handles single chunk or synthesis) ======
def get_gemini_summary(prompt):
    try:
        response = model.generate_content(prompt)
        summary = response.text.strip()
        return summary
    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        # Return a clear error message that indicates API failure
        return "[Error occurred during Gemini API call. Please check your quota or try again.]"


# ====== Interactive Chat with Document Context (Improved) ======
# This function starts a NEW chat conversation and sends chunks as initial context
def interactive_document_chat(chunks, topic, purpose, audience): # Now accepts chunks
    print("\n--- Starting Interactive Chat ---")
    print("Ask questions about the document content. (Enter 'exit' to quit)")
    # Warning about potential token usage for very long documents
    print("⚠️ Note: For very long documents, providing all chunks to the chat may consume significant tokens.")

    # Start a new chat conversation specifically for this interaction
    convo_chat = model.start_chat(history=[])

    # Provide the document content as initial context by sending the chunks
    # This uses more tokens upfront but gives Gemini access to the text.
    print("⏳ Providing document content to the chat model...")
    try:
        # Send initial context setting prompt
        initial_context_prompt = f"""
You are JARVIS, an AI assisting with questions about a document.
The document's topic is: {topic}
Its purpose is: {purpose}
It's for audience: {audience}

I will now provide you with the content of the document in several parts. Please read and process this content so you can answer questions about it.
"""
        convo_chat.send_message(initial_context_prompt)

        # Send each chunk to the conversation history
        for i, chunk in enumerate(chunks):
            print(f"Sending chunk {i+1}/{len(chunks)} to chat context...")
            # Send the chunk content. Add a brief prefix to identify it.
            chunk_message = f"--- Document Part {i+1} ---\n{chunk}"
            convo_chat.send_message(chunk_message)
        print("✅ Document content provided to chat context.")
        print("\nReady to answer questions.")

    except Exception as e:
        print(f"❌ Error providing document content to chat context: {e}")
        print("The chat may not be able to answer questions about the document.")


    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ['exit', 'quit', 'stop']:
            print("🛑 Exiting the chat.")
            break

        if not user_message:
            continue # Skip empty messages

        try:
             # Send the user's question to the chat conversation
             # Gemini now has the chunks in its history to refer to (within limits)
             response = convo_chat.send_message(user_message)
             print(f"JARVIS: {response.text.strip()}")
        except Exception as e:
             print(f"Error during interactive chat: {e}")
             print("Please try your question again.")

   # Collect Context

# ====== Main Script ======
def main(document_title, document_topic, purpose, audience, file_path):
    # print("\n🤖 Welcome to JARVIS Document Summarizer!\n")

    if not os.path.exists(file_path) or not (file_path.lower().endswith(".pdf") or file_path.lower().endswith(".docx")):
        print("Invalid file path. Please provide a PDF or DOCX file.")
        return

 

    raw_text = ""
    if file_path.lower().endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        raw_text = extract_text_from_docx(file_path)

    if not raw_text:
        print("Could not extract text from the document.")
        return

    # --- Summarization Process ---
    speak("Starting the Summarization process Sir.")
    chunks = chunk_text_smart(raw_text)

    if not chunks:
        speak("No content chunks were created from the document.")
        return

    all_chunk_summaries = []

    # Summarize each chunk independently
    for i, chunk in enumerate(chunks):
        # speak(f"\n⏳ Summarizing chunk {i + 1}/{len(chunks)}...")
        chunk_prompt = generate_chunk_prompt(chunk, document_topic, purpose, audience)
        summary = get_gemini_summary(chunk_prompt)
        all_chunk_summaries.append(summary)
        # speak(f"✅ Chunk {i + 1} summarized.")

    # Synthesize individual summaries into an overall summary
    synthesized_summary = None
    # Only attempt synthesis if at least one chunk summary was successful and not an error message
    if all_chunk_summaries and not all(s.startswith("[Error occurred:") for s in all_chunk_summaries):
        speak("Synthesizing overall summary Sir.")
        synthesis_prompt = generate_synthesis_prompt(all_chunk_summaries, document_title, document_topic, purpose, audience)
        synthesized_summary = get_gemini_summary(synthesis_prompt)
        speak("Overall synthesis completed succesfully.")
    elif all_chunk_summaries:
        speak("No successful chunk summaries were generated, skipping overall synthesis.")
    else:
         speak("No chunk summaries were generated, skipping overall synthesis.")


    # --- Report Generation ---
    output_path_base = os.path.splitext(os.path.basename(file_path))[0]
    output_filename = f"{output_path_base}_JARVIS_Summary_Report.docx"
    saved_path = save_summary_to_docx(synthesized_summary, all_chunk_summaries, output_filename, document_title, document_topic, file_path)
    speak("The overall summary report is generated  and saved in our directory Sir.")

    # --- Open the saved report ---
    if saved_path and os.path.exists(saved_path):
        # print(f"The Report is saved at: {saved_path}")
        speak("Attempting to open the file")
        try:
            if os.name == "nt": # Windows
                os.startfile(saved_path)
                speak("File opened successfully.")
            # elif sys.platform == "darwin": # macOS
            #     subprocess.run(["open", saved_path], check=True)
            # elif os.name == "posix": # Linux/Unix
            #     if os.system("command -v xdg-open > /dev/null") == 0:
            #         subprocess.run(["xdg-open", saved_path], check=True)
            #     else:
            #         print("ℹ️ 'xdg-open' command not found. Could not automatically open the document. Please open it manually.")
            # else:
            #     print("ℹ️ Could not automatically open the document. Please open it manually.")
        except FileNotFoundError:
            speak(f"Error: Command to open file not found.")
        except subprocess.CalledProcessError as e:
            speak(f"Error opening document: {e}")
        except Exception as e:
            speak(f"An unexpected error occurred while trying to open the document: {e}")

    # --- Interactive Chat ---
    # Call the interactive chat function AFTER summarization and report generation
    # Pass the chunks so the chat can receive the document content

    # interactive_document_chat(chunks, document_topic, purpose, audience)


if __name__ == "__main__":
    document_title = input("📝 Enter the title of the document: ").strip()
    document_topic = input("📚 What is the document about? ").strip()
    purpose = input("🎯 What is the purpose of the summary? (e.g., exam prep, revision, research): ").strip()
    audience = input("👥 Who is this summary for? (e.g., student, teacher, researcher): ").strip()
    file_path = input("📂 Enter full path to the document (PDF or DOCX): ").strip()
    main(document_title, document_topic, purpose, audience, file_path)