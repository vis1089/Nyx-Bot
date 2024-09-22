import discord
from discord.ext import commands
from discord.commands import option
import aiohttp
from io import BytesIO
import os
from PIL import Image
import pytesseract

# Example voices list, replace with actual voices from the ElevenLabs API
voices = [
    {'name': 'Voice1', 'voice_id': 'abc123'},
    {'name': 'Voice2', 'voice_id': 'def456'}
]

# Define your bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

# Set the path for Tesseract if it's not in your PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to make text-to-speech API call to ElevenLabs
async def text_to_speech(input_text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        'accept': 'audio/mpeg',
        'content-type': 'application/json',
        'xi-api-key': os.getenv("ELEVEN_LABS_API_KEY")  # Add your ElevenLabs API key to environment variables
    }
    data = {'text': input_text}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                print(f"Error: {resp.status} - {await resp.text()}")
                return None

# Helper function to find the voice ID for a given voice name
def voice_id_for_name(name):
    for voice in voices:
        if voice['name'] == name:
            return voice['voice_id']
    return None 

# Slash command for text-to-speech
@bot.slash_command(
    name="text2speech",
    description="Convert your text to speech with your selected voice"
)
@option('text', description="Text to Convert to Speech", required=True)
@option('voice', description="Choose a Voice", choices=[voice['name'] for voice in voices], required=True)
async def text2speech(ctx, text: str, voice: str):
    await ctx.defer()  # Acknowledge the command while processing the TTS
    await ctx.edit(content="Generating TTS...")

    voice_id = voice_id_for_name(voice)
    if not voice_id:
        await ctx.respond("Error: Invalid voice selection.")
        return

    audio_data = await text_to_speech(text, voice_id)
    if audio_data:
        with BytesIO(audio_data) as audio_file:
            await ctx.respond(file=discord.File(fp=audio_file, filename='speech.mp3'))
    else:
        await ctx.respond("Error while generating speech from text.")

# Slash command for OCR
@bot.slash_command(
    name="ocr",
    description="Extract text from an image"
)
@option('image', description="Upload an image for OCR", required=True)
async def ocr(ctx, image: discord.Attachment):
    await ctx.defer()  # Acknowledge the command while processing the OCR
    await ctx.edit(content="Processing image...")

    # Download the image
    image_data = await image.read()
    image_file = BytesIO(image_data)

    try:
        # Open the image and perform OCR
        img = Image.open(image_file)
        extracted_text = pytesseract.image_to_string(img)

        if extracted_text.strip():
            await ctx.respond(f"Extracted Text:\n{extracted_text}")
        else:
            await ctx.respond("No text found in the image.")
    except Exception as e:
        await ctx.respond(f"Error while processing image: {str(e)}")

# Keep the bot alive (optional, for environments where this is necessary)
# keep_alive.keep_alive()

# Run the bot with your Discord token
bot.run(os.environ['DISCORD_TOKEN'])
