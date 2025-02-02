import discord
from openai import OpenAI
import openai
import io
from discord.ext import commands
from dotenv import load_dotenv
import os
client = OpenAI()
#bot = commands.Bot(command_prefix="!")
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
# print(f"OpenAI API Key: {openai_api_key}")

# response = client.images.generate(
#     model="dall-e-3",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="standard",
#     n=1,
# )

# print(response.data[0].url)

def generate_image(prompt):
    response =client.images.generate(
        model ="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality = "standard",
    )
    image_url = response.data[0].url
    print(image_url)
    return image_url

generate_image("lunar new year")
# @bot.command()
# async def generate_image(ctx, *, prompt: str):
#     try:
#         # Call OpenAI's DALL·E API
#         response = openai.Image.create(
#             prompt=prompt,
#             n=1,
#             size="512x512"
#         )
#         # Get the image URL from the response
#         image_url = response['data'][0]['url']

#         # Send the generated image to Discord
#         await ctx.send(image_url)
#     except Exception as e:
#         await ctx.send(f"Error generating image: {e}")