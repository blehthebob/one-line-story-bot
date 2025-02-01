import discord
from dotenv import load_dotenv
import os

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

if __name__ == '__main__':
    load_dotenv()
    client = MyClient(intents=intents)
    client.run(os.getenv('BOT_TOKEN'))