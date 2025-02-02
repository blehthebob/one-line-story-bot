import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from liveStoryMem import *
from llm_utils import *
import json
from random import randint, choice

""" 
    TODO:
    - !create, !personality, !join to join the story, !start to begin writing
    - Randomly select eligible user for next line
    - Finalise story
    - Print out final story (@user1: line1, @bot: line 2, etc)
"""

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

class StoryId():
    def __init__(self):
        self.id = 0

    def get(self):
        self.id += 1
        return self.id

current_story_id = StoryId()
poll_time = 30

personality = None
default_personality_options = ["sad", "funny", "mysterious", "action-packed", "fantasy/sci-fi"]
users = set()
length = 0
primed = False

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}')
        
@bot.command(brief="Start a new story with a given number of lines")
async def story(ctx, lines: int = commands.parameter(
    default=5,
    description="The total number of lines in the story"
)):
    global length, primed, personality, users
    length = lines
    primed = True
    personality = None
    users = set()
    await ctx.send(f"Story of length {length} lines initiated. Use !join to take part and !start to begin writing.")
   
@bot.command(brief="Register as a writer for the story")
async def join(ctx):
    users.add(ctx.author)
    await ctx.send(f'{ctx.author.name} has joined the story!')

@bot.command(brief="Set the tone of the story e.g. sad, funny, ...")
async def personality(ctx, p: str):
    global personality
    personality = p
    await ctx.send(f"Personality: {personality}")
 
@bot.command(brief="Begin writing the story")
async def start(ctx):
    if not primed:
        return
    global personality
    channel = ctx.channel
    def check(msg):
        return msg.author in users and msg.channel == channel
    turn = 1
    await ctx.send(f'Story time! Let\'s write {length} lines together! You start:')
    message = await bot.wait_for('message', check=check)
    id = current_story_id.get()
    if personality is None:
        # Randomly select out of a list
        personality = choice(default_personality_options)
    
    create_story(id, message.content, personality, message.author.name)
    print(f"Sent by {message.author.name}")
    
    for _ in range(length - 1):
        if turn == 0: # user
            await ctx.send('Your turn! What comes next?')
            message = await bot.wait_for('message', check=lambda m: m.author in users)
            
            add_new_line_and_update_by_id(id, message.content, message.author.name)
        else: # bot
            reply = await generate_reply(id)
            print(reply)
            messages = json.loads(reply)
            options = [m["text"] for m in messages]
          
            poll = await create_poll(ctx, f"You have {poll_time} seconds to vote ... ", options[0:3]) 
            await asyncio.sleep(poll_time)         
            result = await get_poll_result(ctx, poll)
            
            embed = discord.Embed(description=options[result], color=discord.Color.blue())
            await ctx.send(embed=embed)

            add_new_line_and_update_by_id(id, options[result], "bot")
        
        turn = 1 - turn
    
    # finalise story
    await finalise(ctx, id)
    await ctx.send(f'The end!')
    
async def finalise(ctx, id):
    data, imgurl = finalize_story(id)
    story = data["currentStoryText"]
    embed = discord.Embed(title= active_stories[id]["title"], description=story, color=discord.Color.blue())
    embed.set_image(url=imgurl)
    
    await ctx.send(embed=embed)
    
    

async def create_poll(ctx, question, options):
    embed = discord.Embed(title=f"What happens next? {question}", color=0x00ff00)
    reactions = ['1️⃣', '2️⃣', '3️⃣']
    
    for i, option in enumerate(options):
        embed.add_field(name=f'Option {i + 1}', value=option, inline=False)
    
    poll_message = await ctx.send(embed=embed)
    
    for i in range(len(options)):
        await poll_message.add_reaction(reactions[i])
    
    return poll_message

async def get_poll_result(ctx, poll_message):
    poll_message = await ctx.channel.fetch_message(poll_message.id)
    results = {reaction.emoji: reaction.count - 1 for reaction in poll_message.reactions}  # Subtract 1 to exclude the bot's own reaction
    max_votes = 0
    poll_response = ""
    
    for answer, votes in results.items():
        if votes > max_votes:
            max_votes = votes
            poll_response = answer

    if max_votes == 0:
        return randint(0, 2)
    
    reactions = ['1️⃣', '2️⃣', '3️⃣']
    return reactions.index(poll_response)

# @bot.command()
# async def story_user(ctx,
#                      users: commands.Greedy[discord.User] = commands.parameter(
#                          description="The users participating in the story",
#                          default = []),
#                      lines: int = commands.parameter(
#                          default=5,
#                          description="The total number of lines in the story"
#                          )):
#     chat_history_2 = []
#     turn = 0
#     userCount = 0
#     if len(users) == 0:
#         users = [ctx.author]

#     await ctx.send(f'Story time! Let\'s write {lines} lines together! You start:')

#     for _ in range(lines):
#         if turn == 0: # user
#             message = await bot.wait_for('message', check=lambda m: m.author == users[userCount])
#             chat_history_2.append(message.content)
#             userCount = (userCount + 1) % len(users)
#         else: # bot
#             message = await generate_reply()
#             chat_history_2.append(message)
#             await ctx.send('message')
#         turn = 1 - turn
        
#     await ctx.send(f'Received: {chat_history}')

async def generate_reply(story_id: int):
    return generate_next_line_candidates_list(
        active_stories[story_id]['currentStoryText'],
        active_stories[story_id]['storyMetadata']['promptPersonality'],
    )
        

def main():
    load_dotenv()
    bot.run(os.getenv('BOT_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())