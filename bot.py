import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

chat_history = []

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)
    
# can we have like !story user1 user2 user3

# !start ___
# receive a cmd(line_limit)
# begin listening for story
# receive 1 line of story
# feed to ai
# get ai return
# make poll
# edit poll? into poll winner
# rand select user for next line
# repeat until line limit
# gen ending
# with image

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}')
        
@bot.command()
async def story(ctx, lines: int = commands.parameter(
    default=5,
    description="The total number of lines in the story"
)):
    turn = 0
    await ctx.send(f'Story time! Let\'s write {lines} lines together! You start!')
    for _ in range(lines):
        if turn == 0: # user
            await ctx.send(f'Give me a cool line:')
            message = await bot.wait_for('message')
            chat_history.append(message.content)
        else: # bot
            messages = await send_reply()

            p = discord.Poll(question="Which line should come next?", duration=timedelta(hours=1.0))
            for message in messages:
                p.add_answer(text=message)
            p_message = await ctx.send(poll=p)
            
            await asyncio.sleep(20)
            await p.end()
            
            updated_message = await ctx.channel.fetch_message(p_message.id)
            poll_results = {answer.text: answer.vote_count for answer in updated_message.poll.answers}

            max_votes = 0
            poll_response = poll_results.keys()[0]
            for answer, votes in poll_results.items():
                if int(votes) > max_votes:
                    max_votes = int(votes)
                    poll_response = answer
            
            chat_history.append(poll_response)
            await ctx.send(poll_response)
        turn = 1 - turn
        
    await ctx.send(f'Received: {chat_history}')

@bot.command()
async def story_user(ctx,
                     users: commands.Greedy[discord.User] = commands.parameter(
                         description="The users participating in the story",
                         default = []),
                     lines: int = commands.parameter(
                         default=5,
                         description="The total number of lines in the story"
                         )):
    chat_history_2 = []
    turn = 0
    userCount = 0
    if len(users) == 0:
        users = [ctx.author]

    await ctx.send(f'Story time! Let\'s write {lines} lines together! You start:')

    for _ in range(lines):
        if turn == 0: # user
            message = await bot.wait_for('message', check=lambda m: m.author == users[userCount])
            chat_history_2.append(message.content)
            userCount = (userCount + 1) % len(users)
        else: # bot
            message = await send_reply()
            chat_history_2.append(message)
            await ctx.send('message')
        turn = 1 - turn
        
    await ctx.send(f'Received: {chat_history}')
    
async def send_reply():
    return ['hi', 'there', 'hoang xdd']

def main():
    load_dotenv()
    bot.run(os.getenv('BOT_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())