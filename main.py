import discord
from discord.ext import commands
import aiohttp
import json
import os

ocr_key = os.environ['OCR_KEY']
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="xr7.", intents=intents)

async def ocr_space_url(url, overlay=False, api_key=ocr_key, language='eng'):
    payload = {
        'url': url,
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
        'OCREngine': 2,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.ocr.space/parse/image', data=payload) as response:
            result = await response.text()
            return result

def split_response(response, max_length=1900):
    lines = response.splitlines()
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n"
            current_chunk += line

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    if message.attachments:
        attachment = message.attachments[0]
        
        # Check for allowed file types, including GIF
        allowed_file_types = ['.png', '.jpg', '.jpeg', '.gif']
        if not any(attachment.filename.lower().endswith(ext) for ext in allowed_file_types):
            await message.reply("Please upload a PNG, JPG, or GIF image.")
            return
        
        # Check for file size limit
        if attachment.size > 1024 * 1024:
            await message.reply("Please send an image under 1MB.")
            return
        
        await message.add_reaction('🔍')
        attachment_url = attachment.url
        ocr_result = await ocr_space_url(url=attachment_url, overlay=False, api_key=ocr_key, language='eng')
        
        ocr_data = json.loads(ocr_result)
        if "ParsedResults" in ocr_data and len(ocr_data["ParsedResults"]) > 0 and "ParsedText" in ocr_data["ParsedResults"][0]:
            recognized_text = ocr_data["ParsedResults"][0]["ParsedText"]
            response_chunks = split_response(recognized_text)
            for chunk in response_chunks:
                await message.channel.send(chunk)
        else:
            await message.reply("No text recognized in the image.")



bot.run(os.environ['DISCORD_TOKEN'])
