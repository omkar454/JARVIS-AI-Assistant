import os
import sys
import subprocess
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from MainJarvis_TaskExecution import speak

# ========== CONFIGURATION ==========
genai.configure(api_key=os.getenv("GEMINI_API_2"))  # Replace with secure API retrieval
model = genai.GenerativeModel("gemini-1.5-pro")

# ========== UTILITIES ==========

def configure_fonts(paragraph, size, font):
    for run in paragraph.runs:
        run.font.name = font
        run.font.size = Pt(size)

def add_content_to_doc(doc, content_lines, para_font_size, heading_font_size, line_spacing, font_style):
    for line in content_lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("### "):
            heading = doc.add_heading(line[4:], level=3)
            configure_fonts(heading, heading_font_size - 2, font_style)
        elif line.startswith("## "):
            heading = doc.add_heading(line[3:], level=2)
            configure_fonts(heading, heading_font_size, font_style)
        elif line.startswith("# "):
            heading = doc.add_heading(line[2:], level=1)
            configure_fonts(heading, heading_font_size + 2, font_style)
        elif line.startswith("- "):
            bullet = doc.add_paragraph(line[2:], style='List Bullet')
            configure_fonts(bullet, para_font_size, font_style)
        else:
            p = doc.add_paragraph(line)
            p.paragraph_format.line_spacing = line_spacing
            configure_fonts(p, para_font_size, font_style)

def generate_content_from_prompt(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None

def save_and_open_document(doc, filename):
    try:
        doc.save(filename)
        print(f"\n✅ Document saved as: {filename}")
        if os.name == "nt":
            os.startfile(filename)
        elif sys.platform == "darwin":
            subprocess.run(["open", filename], check=True)
        elif os.name == "posix":
            subprocess.run(["xdg-open", filename], check=True)
    except Exception as e:
        print(f"⚠️ Error handling document: {e}")

# ========== MAIN LOGIC ==========

def create_general_document(topic, audience, purpose, tone, pages, filename, para_size, heading_size, spacing, font_style):
    length = "short" if pages == "1" else "medium" if pages in ["2", "3"] else "long"
    prompt = (
        f"Write a {length} professional document on the topic '{topic}'. "
        f"Target audience: {audience}. Purpose: {purpose}. Tone: {tone}. "
        f"Include a title, introduction, 2-4 main headings with 1-2 paragraphs each, bullet points where needed, and a conclusion. "
        f"Avoid markdown symbols. Provide plain text."
    )

    content = generate_content_from_prompt(prompt)
    if not content:
        return

    doc = Document()
    title = doc.add_heading(topic, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    configure_fonts(title, heading_size + 4, font_style)

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("introduction") or line.lower().startswith("conclusion") or any(
                t in line.lower() for t in ["section", "chapter", "part"]):
            heading = doc.add_heading(line, level=1)
            configure_fonts(heading, heading_size, font_style)
        elif line.startswith("- "):
            bullet = doc.add_paragraph(line[2:], style='List Bullet')
            configure_fonts(bullet, para_size, font_style)
        else:
            p = doc.add_paragraph(line)
            p.paragraph_format.line_spacing = spacing
            configure_fonts(p, para_size, font_style)

    speak("General document generated successfully and saved in our directory.")
    speak("Attempting to open the document")
    save_and_open_document(doc, filename)
    speak("Document opened successfully")

def create_engineering_notes(topic, detail_level, concepts, format_style, filename, para_size, heading_size, spacing, font_style):
    prompt = (
        f"Generate comprehensive engineering notes on the topic '{topic}'. "
        f"Detail level: {detail_level}. Format: {format_style}. "
        f"Focus on key concepts, explanations, and practical aspects. "
        f"Use markdown structure: # for title, ## for major sections, ### for sub-points, - for bullet points."
    )

    content = generate_content_from_prompt(prompt)
    if not content:
        return

    doc = Document()
    title = doc.add_heading(topic, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    configure_fonts(title, heading_size + 4, font_style)

    add_content_to_doc(doc, content.split("\n"), para_size, heading_size, spacing, font_style)
    speak("Engineering notes generated successfully and saved in our directory.")
    speak("Attempting to open the notes document")
    save_and_open_document(doc, filename)
    speak("Document opened succesfully")
    

# ========== OPTIONAL: Interactive Mode ==========
# topic = input("📘 Document topic: ").strip()
#         audience = input("👤 Audience: ").strip()
#         purpose = input("🎯 Purpose: ").strip()
#         tone = input("🗣️ Tone: ").strip()
#         pages = input("📄 Approx. pages (e.g., 1-5): ").strip()
def general_docx(topic, audience, purpose, tone, pages, filename_base):
        # topic = input("📘 Document topic: ").strip()
        # audience = input("👤 Audience: ").strip()
        # purpose = input("🎯 Purpose: ").strip()
        # tone = input("🗣️ Tone: ").strip()
        # pages = input("📄 Approx. pages (e.g., 1-5): ").strip()
        create_general_document(topic, audience, purpose, tone, pages, f"{filename_base}_GeneralDoc.docx", para_size=14, heading_size=16, spacing=1.5, font_style="Times New Roman")

def engineering_notes(topic, detail, concepts, notes_format, filename_base):
        create_engineering_notes(topic, detail, concepts, notes_format, f"{filename_base}_EngineeringNotes.docx", para_size=14, heading_size=16, spacing=1.5, font_style="Times New Roman")


def interactive_mode(mode, filename_base, para_size, heading_size, spacing, font_style):


    if mode == "1":
        topic = input("📘 Document topic: ").strip()
        audience = input("👤 Audience: ").strip()
        purpose = input("🎯 Purpose: ").strip()
        tone = input("🗣️ Tone: ").strip()
        pages = input("📄 Approx. pages (e.g., 1-5): ").strip()
        create_general_document(topic, audience, purpose, tone, pages, f"{filename_base}_GeneralDoc.docx", para_size, heading_size, spacing, font_style)

    elif mode == "2":
        topic = input("📘 Topic: ").strip()
        detail = input("📈 Detail level (basic, intermediate, in-depth): ").strip() or "intermediate"
        concepts = input("💡 Include concepts (comma-separated): ").strip()
        notes_format = input("📝 Notes format (e.g., Q&A, structured): ").strip() or "structured sections"
        create_engineering_notes(topic, detail, concepts, notes_format, f"{filename_base}_EngineeringNotes.docx", para_size, heading_size, spacing, font_style)

    else:
        print("❌ Invalid selection.")

# ========== RUN INTERACTIVE ==========
if __name__ == "__main__":
    print("🚀 JARVIS Document Creator")
    print("1. General Document")
    print("2. Engineering Notes")
    mode = input("Choose (1 or 2): ").strip()
    filename_base = input("💾 Output filename (no extension): ").strip() or "GeneratedDoc"
    para_size = int(input("🔠 Paragraph font size: ") or 12)
    heading_size = int(input("🔠 Heading font size: ") or 16)
    spacing = float(input("📏 Line spacing: ") or 1.15)
    font_style = input("🖋️ Font style (default: Times New Roman): ").strip() or "Times New Roman"
    interactive_mode(mode, filename_base, para_size, heading_size, spacing, font_style)
