import os
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, MSO_VERTICAL_ANCHOR
from pptx.enum.dml import MSO_THEME_COLOR_INDEX
import requests
# import uuid # Not used
from PIL import Image
import io
import sys
import subprocess
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_3")
SERP_API_KEY = os.getenv("SERP_API") # <<< REPLACE WITH YOUR ACTUAL KEY

SERP_API_URL = "https://serpapi.com/search"

DEFAULT_THEME_PATH = "" # e.g., "C:\\Users\\YourName\\Documents\\Custom Office Templates\\MyTheme.thmx"


# ====== API Key Checks ======
if GEMINI_API_KEY is None or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("❌ GEMINI_API_KEY not set. Please set it in the script or as an environment variable.")
    sys.exit(1)

# Don't exit if SerpAPI key is missing, just disable image search
if SERP_API_KEY is None or SERP_API_KEY == "YOUR_SERP_API_KEY_HERE":
    print("⚠️ SERP_API_KEY not set. Image search will be skipped.")

# ====== Gemini Setup ======
genai.configure(api_key=GEMINI_API_KEY)
# Added safety settings to handle potential harmful content gracefully
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
# Use a model that's good at following instructions
try:
    model = genai.GenerativeModel("gemini-1.5-pro", safety_settings=safety_settings)
    # Simple test to check if the API key works and model is accessible
    model.generate_content("Ping", stream=True, request_options={"timeout": 10}) # Short timeout for test
except Exception as e:
    print(f"❌ Failed to connect to Gemini API or model. Check your API key and network connection: {e}")
    sys.exit(1)


# ====== Get Image URL from SERP API ======
def fetch_image_url(query):
    """Fetches the first image URL for a given query using SerpAPI."""
    if not SERP_API_KEY or SERP_API_KEY == "YOUR_SERP_API_KEY_HERE":
        # Message is printed at startup, no need to repeat for every image attempt
        return None

    params = {
        "q": query,
        "tbm": "isch", # Image search
        "api_key": SERP_API_KEY,
        "ijn": "0" # Page number (0 for first page)
    }
    print(f"🔍 Searching for image: '{query}'...")
    try:
        # Added timeout
        res = requests.get(SERP_API_URL, params=params, timeout=15).json()
        # Get the first image result URL
        first_image_result = res.get("images_results", [{}])[0]
        url = first_image_result.get("original", first_image_result.get("thumbnail")) # Try original, fallback to thumbnail

        if url and url.startswith("http"): # Basic validation
             print(f"✨ Found image URL: {url}")
             return url
        else:
            print(f"⚠️ No suitable image URL found for '{query}'.")
            return None

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out for image search '{query}'.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching image URL for '{query}': {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error fetching image URL for '{query}': {e}")
        return None

# ====== Get Content from Gemini (Text Parsing) ======
def generate_slides(topic, num_slides, audience, purpose, tone):
    """Generates presentation content using text parsing from Gemini."""

    # --- ADDED: Convert num_slides to integer ---
    # Add error handling in case num_slides is not a valid number string
    try:
        num_slides_int = int(num_slides)
        # Optional: Add a check for a reasonable number of slides
        if num_slides_int <= 0:
             print(f"Warning: Invalid number of slides ({num_slides}). Must be at least 1.")
             return None # Or handle as appropriate
    except ValueError:
        print(f"Error: Invalid input for number of slides: '{num_slides}'. Must be a whole number.")
        return None # Exit the function if conversion fails

    slides_data = []
    # Restoring the original prompt format requesting specific text lines
    # --- MODIFIED PROMPT for more detail (using num_slides_int) ---
    prompt = (

        # Use the integer version here
        f"Create a {num_slides_int}-slide professional presentation on '{topic}' for an audience of {audience}. "
        f"The purpose is to {purpose}, and the tone should be {tone}. "
        # Use num_slides_int in the calculation and comparison
        f"Include a title slide, {max(0, num_slides_int - 2)} content slides, and a conclusion slide (if num_slides_int > 1). "
        f"For content and conclusion slides, provide 3-5 DETAILED and informative bullet points. Each point should be 1-3 sentences, explaining the key information accurately, with examples or data where relevant. "
        f"Suggest 1-2 highly relevant keywords for images for each slide. "
        f"For important terms within bullet points, use markdown bold formatting (e.g., **Important Term**). "
        f"Provide the output for each slide clearly marked like this:\n\n"
        f"Slide Title: [Concise Title]\n"
        f"Slide Content:\n"
        f"- [Detailed Key Point 1 (1-3 sentences)]\n"
        f"- [Detailed Key Point 2 (1-3 sentences)]\n"
        f"- [Detailed Key Point 3 (1-3 sentences)]\n"
        f"Image Keywords: [keyword1], [keyword2]\n\n"
        f"Do not include extra text, conversation, or markdown formatting outside of the specified format for each slide. Ensure each slide block starts with 'Slide Title:'. "
    )

    print("\n--- Gemini Prompt ---")
    # print(prompt) # Uncomment to see the full prompt
    # Use the integer version here
    print(f"Generating {num_slides_int} slides for '{topic}' using text parsing...")
    print("--- End of Prompt ---")

    try:
        # Increased timeout for content generation
        res = model.generate_content(prompt, request_options={"timeout": 120})
        raw_text = res.text.strip()

        # Basic splitting by double newline, similar to original logic
        blocks = raw_text.split("\n\n")
        # print(f"\n--- Raw Gemini Output (Split by '\\n\\n') ---\n{blocks}\n--- End of Raw Output ---") # Uncomment for debugging

        slides_data = [] # Reset in case of multiple calls
        current_slide_info = {}
        for block in blocks:
            lines = block.strip().split('\n')
            # print(f"Processing block lines: {lines}") # Uncomment for debugging

            # Check if the block starts a new slide based on the expected "Slide Title:" format
            title_line = next((line for line in lines if line.startswith("Slide Title:")), None)
            if title_line:
                # If we found a title, and we were processing a previous slide, save it
                # Only append if we have some meaningful data for the previous slide
                if current_slide_info and (current_slide_info.get("title") or current_slide_info.get("content") or current_slide_info.get("image_keywords")):
                    slides_data.append(current_slide_info)
                    print(f"Appended previous slide data: {current_slide_info.get('title', 'Untitled')}")

                # Start a new slide
                current_slide_info = {}
                current_slide_info["title"] = title_line.replace("Slide Title:", "").strip()
                current_slide_info["content"] = [] # Initialize content list
                current_slide_info["image_keywords"] = [] # Initialize keywords list
                # Layout and design notes aren't reliably parsed in this simple method, so we omit them here

                # Parse lines within this block for content and keywords
                parsing_content = False
                for line in lines:
                     line = line.strip()
                     if line.startswith("Slide Content:"):
                          parsing_content = True
                          continue
                     elif line.startswith("Image Keywords:"):
                          parsing_content = False # Stop parsing content
                          keywords_str = line.replace("Image Keywords:", "").strip()
                          # Split keywords by comma, clean up spaces and brackets
                          # Handles cases like "[keyword1], [keyword2]" or "keyword1, keyword2"
                          keywords_list = [k.strip().strip('[]') for k in keywords_str.split(',') if k.strip()]
                          current_slide_info["image_keywords"] = keywords_list
                          # print(f"Found keywords: {current_slide_info['image_keywords']}") # Uncomment for debugging
                          break # Assume keywords are at the end of the slide block
                     elif parsing_content and line.startswith("-"):
                          # Assuming bullet points start with '-'
                          point = line.replace("-", "").strip()
                          if point: # Only add if not empty after stripping
                            current_slide_info["content"].append(point)
                          # print(f"Added content point: {point}") # Uncomment for debugging
                     # Ignore other lines if they don't match expected formats

        # Append the last slide after the loop finishes
        # Check if current_slide_info is not empty before appending
        if current_slide_info and (current_slide_info.get("title") or current_slide_info.get("content") or current_slide_info.get("image_keywords")):
            slides_data.append(current_slide_info)
            print(f"Appended final slide data: {current_slide_info.get('title', 'Untitled')}")


    except Exception as e:
        print(f"❌ Error generating content from Gemini or parsing response: {e}")
        # If content generation or parsing fails, return empty list
        return []
    # Ensure we return only up to the requested number of slides
    # Added a check that slides_data is not empty before slicing
    final_slides = slides_data[:num_slides] if slides_data else []
    print(f"\n--- Parsed Slides Data ({len(final_slides)} slides) ---\n{final_slides}\n--- End of Slides Data ---")
    return final_slides

# ====== Create PPT with Layout and Styling (Manual Positioning) ======
def create_ppt(slides, output="Generated_Presentation.pptx"): # Changed default name
    prs = Presentation()
    # --- Apply Theme (.thmx) ---
    # Applying a theme file (.thmx) can change colors/fonts but doesn't change layout structure
    if DEFAULT_THEME_PATH and os.path.exists(DEFAULT_THEME_PATH):
        try:
            prs.theme = DEFAULT_THEME_PATH # Apply theme from .thmx file
            print(f"✨ Applied theme from '{DEFAULT_THEME_PATH}'.")
        except Exception as e:
            print(f"❌ Error applying theme from '{DEFAULT_THEME_PATH}': {e}")
            print("Continuing with default blank theme.")
    else:
        if DEFAULT_THEME_PATH:
            print(f"⚠️ Theme file not found at '{DEFAULT_THEME_PATH}'.")
        print("Using default presentation theme.")


    # Use the blank layout (index 6) for manual positioning
    # This layout has no predefined placeholders, giving us a blank canvas.
    blank_slide_layout = prs.slide_layouts[6]

    for i, slide_data in enumerate(slides):
        print(f"\n--- Adding Slide {i+1}: {slide_data.get('title', 'Untitled')} ---")
        slide = prs.slides.add_slide(blank_slide_layout)

        # --- Define Layout Grid (Manual Positioning) ---
        # These ratios define the size and position of content and image boxes relative to slide size.
        # Adjust these ratios if the layout isn't satisfactory.
        slide_width = prs.slide_width
        slide_height = prs.slide_height

        # Define proportional dimensions
        content_col_width_ratio = 0.45 # Proportion of slide width for content column (slightly increased)
        image_col_width_ratio = 0.25 # Proportion of slide width for each image column (slightly decreased)
        space_between_cols_ratio = 0.025 # Small gap between columns

        title_row_height_ratio = 0.10 # Proportion of slide height for the title area
        content_image_height_ratio = 0.65 # Proportion of slide height for the main content/image area
        bottom_bar_height_ratio = 0.10 # Proportion of slide height for the bottom bar

        # Calculate absolute dimensions (using slide units like Emu, but Inches() helps)
        # Using Inches() for calculations makes them more readable
        slide_width_in = slide_width.inches
        slide_height_in = slide_height.inches

        # Margins in inches
        margin_left_in = slide_width_in * 0.03 # 3% margin
        margin_top_in = slide_height_in * 0.03 # 3% margin
        # Note: Right and bottom margins are implicitly handled by element widths/heights and total slide size

        # Calculated widths and heights in inches
        content_width_in = slide_width_in * content_col_width_ratio
        image_width_in = slide_width_in * image_col_width_ratio
        space_between_cols_in = slide_width_in * space_between_cols_ratio

        title_height_in = slide_height_in * title_row_height_ratio
        content_image_height_in = slide_height_in * content_image_height_ratio
        bottom_bar_height_in = slide_height_in * bottom_bar_height_ratio


        # --- Title Text Box ---
        # Position below top margin, spanning most of the width
        title_left = Inches(margin_left_in)
        title_top = Inches(margin_top_in)
        title_textbox_width = Inches(slide_width_in - margin_left_in - (slide_width_in * 0.03)) # Title spans most of the width
        title_textbox_height = Inches(title_height_in)
        title_shape = slide.shapes.add_textbox(title_left, title_top, title_textbox_width, title_textbox_height)
        tf_title = title_shape.text_frame
        tf_title.text = slide_data.get("title", "Untitled")
        tf_title.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE # Center text vertically
        tf_title.word_wrap = True # Ensure title wraps if too long

        # Apply formatting: Times New Roman, Bold
        if tf_title.paragraphs: # Check if paragraph exists (it should after setting text)
            p_title = tf_title.paragraphs[0]
            p_title.font.size = Pt(32) # Starting with a large size
            p_title.font.bold = True
            p_title.alignment = MSO_ANCHOR.TOP # Align title left (common)
            p_title.font.name = 'Times New Roman' # Set font

            # Optional: Set title color from theme
            # try:
            #     p_title.font.color.theme_color = MSO_THEME_COLOR_INDEX.ACCENT_1
            # except AttributeError:
            #     pass


        # --- Content Text Box ---
        # Position below title, left column
        content_left = Inches(margin_left_in)
        content_top = Inches(margin_top_in + title_height_in) # Position below title
        content_height = Inches(content_image_height_in)
        content_shape = slide.shapes.add_textbox(content_left, content_top, Inches(content_width_in), content_height)
        tf_content = content_shape.text_frame
        tf_content.vertical_anchor = MSO_VERTICAL_ANCHOR.TOP # Align content to top
        tf_content.word_wrap = True # Ensure text wraps


        # Add bullet points from parsed content with formatting
        content_list = slide_data.get("content", [])
        if content_list:
            tf_content.clear() # Clear any default text in the textbox

            # Add bullet points with potential bold formatting
            for j, point_text in enumerate(content_list):
                p = tf_content.add_paragraph()
                p.level = 0 # Main bullet level (adjust for sub-bullets if needed from AI)

                # Add text with bold formatting for **text** markdown using regex
                # Split the text by occurrences of **...** while keeping the delimiters
                parts = re.split(r'(\*\*.*?\*\*)', point_text)
                for part in parts:
                    run = p.add_run()
                    if part.startswith('**') and part.endswith('**'):
                        run.text = part[2:-2] # Remove the asterisks
                        run.font.bold = True
                    else:
                        run.text = part
                    run.font.name = 'Times New Roman' # Set font for each run
                    run.font.size = Pt(18) # Set a standard font size for bullet points
                    try: run.font.color.theme_color = MSO_THEME_COLOR_INDEX.TEXT_1 # Example color from theme
                    except AttributeError: pass # Fallback if theme color fails

        else:
             # If no content, add a placeholder text or leave blank
             tf_content.text = "Content Not Available"
             if tf_content.paragraphs: # Check if paragraphs list is created
                 p = tf_content.paragraphs[0]
                 p.font.size = Pt(14)
                 p.font.italic = True
                 p.font.name = 'Times New Roman'
                 try: p.font.color.theme_color = MSO_THEME_COLOR_INDEX.TEXT_2
                 except AttributeError: pass


        # --- Images (Manually Positioned) ---
        image_top = Inches(margin_top_in + title_height_in) # Images align vertically with content top
        image_height = Inches(content_image_height_in) # Images have the same height as content block

        image_left_1 = Inches(margin_left_in + content_width_in + space_between_cols_in) # Position image 1 to the right of content
        image_left_2 = Inches(image_left_1.inches + image_width_in + space_between_cols_in) # Position image 2 to the right of image 1

        image_keywords = slide_data.get("image_keywords", [])

        # Add images if keywords and API key are available
        if (SERP_API_KEY is not None and SERP_API_KEY != "YOUR_SERP_API_KEY_HERE") and image_keywords:
            # Add first image if keyword exists
            if len(image_keywords) > 0:
                 print(f"Attempting to add Image 1 for keyword: '{image_keywords[0]}'")
                 # Pass exact position and size to the helper in Inches
                 add_image_to_blank_slide(slide, image_keywords[0], image_left_1, image_top, Inches(image_width_in), image_height)

            # Add second image if keyword exists
            if len(image_keywords) > 1:
                 print(f"Attempting to add Image 2 for keyword: '{image_keywords[1]}'")
                 # Pass exact position and size to the helper in Inches
                 add_image_to_blank_slide(slide, image_keywords[1], image_left_2, image_top, Inches(image_width_in), image_height)

            if len(image_keywords) > 2:
                 print(f"ℹ️ More than 2 image keywords provided. Adding the first two only with this layout.")

        elif image_keywords: # Keywords provided but API key missing
             print("⚠️ SERP_API_KEY is not set. Skipping image insertion.")
        else: # No image keywords provided
             print("ℹ️ No image keywords provided by Gemini for this slide. Skipping image insertion.")


        # --- Bottom Bar (Example Design Element - Manually Positioned) ---
        # Position at the very bottom, spans full width
        bottom_bar_left = Inches(0) # Starts from the left edge
        bottom_bar_top = Inches(slide_height_in - bottom_bar_height_in) # Positioned from the bottom edge
        bottom_bar_width = Inches(slide_width_in) # Spans full width
        bottom_bar_height = Inches(bottom_bar_height_in)
        bottom_bar_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bottom_bar_left, bottom_bar_top, bottom_bar_width, bottom_bar_height)

        # Apply color fill
        background_fill = bottom_bar_shape.fill
        background_fill.solid()
        try:
            background_fill.fore_color.theme_color = MSO_THEME_COLOR_INDEX.ACCENT_2
            background_fill.fore_color.brightness = 0.8 # Make it lighter
        except AttributeError:
            background_fill.fore_color.rgb = RGBColor(200, 200, 200) # Fallback color

        # Remove outline
        background_line = bottom_bar_shape.line
        background_line.fill.background() # Transparent line


    # --- Save Presentation ---
    try:
        # Generate a safer filename from the title of the *first* slide
        first_slide_title = slides[0].get("title", "Generated_Presentation") if slides else "Generated_Presentation"
        safe_title = "".join(c for c in first_slide_title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        if not safe_title: # Fallback if title was empty or invalid chars
            safe_title = "GeneratedPresentation"
        output_filename = f"{safe_title}_Presentation.pptx"

        prs.save(output_filename)
        print(f"\n✅ PPT saved successfully as: {output_filename}")
    except Exception as e:
        print(f"❌ Error saving presentation: {e}")
        # Don't exit, try to open if possible


    # --- Open Presentation ---
    print(f"Attempting to open {output_filename}...")
    try:
        if os.name == "nt": # Windows
            os.startfile(output_filename)
       
    except FileNotFoundError:
        print(f"⚠️ Error: Command to open file not found.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error opening document: {e}")
    except Exception as e:
        print(f"⚠️ An unexpected error occurred while trying to open the document: {e}")


# ====== Helper to add image to a blank slide (Manual Positioning) ======
def add_image_to_blank_slide(slide, keyword, left, top, width, height):
    """Fetches an image and adds it to the slide at specific coordinates and size."""
    if not keyword:
        # Message handled before calling this helper
        return

    image_url = fetch_image_url(keyword) # Uses the fetch_image_url function defined earlier

    if image_url:
        try:
            print(f"Downloading image from URL: {image_url}")
            response = requests.get(image_url, stream=True, timeout=15) # Added timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            img_data = response.content

            # python-pptx requires the image to be in a BytesIO stream
            img_stream = io.BytesIO(img_data)

            # Check and potentially convert WEBP using PIL (requires Pillow)
            try:
                img_stream.seek(0) # Reset position after reading content
                img = Image.open(img_stream)
                if img.format == 'WEBP':
                    print("Converting WEBP image to PNG.")
                    img_stream_png = io.BytesIO()
                    img.save(img_stream_png, 'PNG')
                    img_stream_png.seek(0) # Reset stream position
                    img_stream = img_stream_png # Use the converted stream
                else:
                    img_stream.seek(0) # Reset stream position if not WEBP
            except Exception as e:
                print(f"⚠️ Could not process image format with PIL (maybe not needed or failed): {e}")
             
            try:
                picture = slide.shapes.add_picture(img_stream, left, top, width, height)
                print(f"✅ Image added successfully for '{keyword}'.")
               

            except Exception as e:
                print(f"❌ Failed to add picture for '{keyword}': {e}")

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error downloading image for '{keyword}' ({e.response.status_code}): {e}")
        except requests.exceptions.Timeout:
             print(f"❌ Timeout downloading image for '{keyword}'.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error downloading image for '{keyword}': {e}")
        except Exception as e:
            print(f"❌ Unexpected error processing image for '{keyword}': {e}")

    else:
        print(f"⚠️ No image URL found or error fetching URL for keyword '{keyword}'. Skipping image.")


# ====== MAIN ENTRY ======
if __name__ == "__main__":
    print("🚀 JARVIS Presentation Creator (Manual Layout Version - Attempting more detail/formatting)")
    print("Please ensure your API keys are set in the script or as environment variables.")
    print(f"Configured theme path (for .thmx): {DEFAULT_THEME_PATH if DEFAULT_THEME_PATH else 'None'}")

    topic = input("📘 Enter topic: ").strip()
    audience = input("👤 Target audience: ").strip()
    purpose = input("🎯 Purpose of presentation: ").strip()
    tone = input("🗣️ Desired tone: ").strip()
    try:
        # Recommend minimum slides to ensure Title/Conclusion are possible
        num = int(input("🧮 Number of slides (min 1): "))
        num = max(1, num) # Ensure at least 1 slide
    except ValueError:
        num = 5
        print("⚠️ Invalid number of slides entered. Defaulting to 5.")

    print("\n⏳ Generating content...")
    # Call the text-parsing content generator
    slides = generate_slides(topic, num, audience, purpose, tone)

    if not slides:
        print("❌ Failed to generate slides.")
    else:
        print("🧠 Content ready. Building presentation...")
        # Call the manual layout PPT creator
        create_ppt(slides)