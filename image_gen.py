from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import time
import uuid
from MainJarvis_TaskExecution import speak
import sys

#
GEMINI_API_KEY = os.getenv("GEMINI_API_2")

if GEMINI_API_KEY is None:
    print("❌ GOOGLE_API_KEY environment variable not set. Please set it.")
    sys.exit(1) # Exit if API key is not found

# Initialize Gemini client
try:
    client = genai.Client(api_key=GEMINI_API_KEY) # Pass key during initialization
    
except Exception as e:
    print(f"❌ Failed to initialize Gemini client: {e}")
    sys.exit(1)


# ====== Image Generation Function ======

def generate_and_save_image(prompt: str, output_dir: str = '.', show_image: bool = True) -> tuple[str | None, str | None]:
    """
    Generates an image using the Gemini 2.0 Flash experimental image generation model,
    saves it to a file, and optionally displays the image.

    Args:
        prompt: The image generation prompt.
        output_dir: Optional. The directory where the image should be saved.
                    Defaults to the current working directory.
        show_image: Optional. If True, attempts to display the generated image
                    after saving. Defaults to False.

    Returns:
        A tuple containing the filename of the saved image (or None if failed)
        and any text response from Gemini (or None).
    """
    # --- Input Validation ---
    if not prompt:
        print("⚠️ Error: Prompt cannot be empty.")
        return None, None

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    speak(f" Generating image for prompt: '{prompt}'...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            # model="gemini-1.5-flash", # Alternative model if needed
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"]
            )
        )

        text_output = ""
        image_filename = None

        if not response.candidates:
            speak("Sorry Sir.Unable to generate image.")
            return None, None

        for part in response.candidates[0].content.parts:
            # Handle text part
            if part.text is not None:
                text_output += part.text.strip() + "\n"

            # Handle image part
            elif part.inline_data is not None:
                try:
                    image_bytes = part.inline_data.data
                    image = Image.open(BytesIO(image_bytes))
                    # Generate a unique filename
                    filename = f"gemini_image_{uuid.uuid4().hex[:8]}.png"
                    full_path = os.path.join(output_dir, filename)
                    image.save(full_path)
                    image_filename = full_path
                    speak(f" Image generated successfully and saved in our directory.")
                    print(f"Image saved as {full_path}")

                    if show_image:
                        # Display the image using the default image viewer
                        image.show()
                        speak("Displaying image now.")

                except Exception as e:
                    speak(f"Sorry Sir. Unable to generate image. Please try again later.")
                    print(f"❌ Error processing or saving image: {e}")
                    # Continue to check for text output even if image save fails
                    image_filename = None # Ensure filename is None on failure

        # Return the generated image filename and any text output
        return image_filename, text_output.strip() if text_output else None

    except Exception as e:
        print(f"❌ Failed to generate content: {e}")
        return None, None

# ====== Example Usage (when script is run directly) ======

if __name__ == "__main__":
    print("🖼️ JARVIS Image Generator using Gemini\n")

    # Get user input via command line
    user_prompt = input("✏️ Enter your image generation prompt: ").strip()

    # Call the function to generate and save the image
    generated_image_path, response_text = generate_and_save_image(
        prompt=user_prompt,
        output_dir="generated_images", # Save images to a sub-directory
        show_image=True # Display the image automatically
    )

    if generated_image_path:
        print(f"\nImage generation complete. Image saved at: {generated_image_path}")
    else:
        print("\nImage generation failed.")

    # Show any text response from Gemini
    if response_text:
        print("\n📝 Gemini Response Text:")
        print(response_text)