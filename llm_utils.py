import os
from openai import OpenAI
from dotenv import load_dotenv
import re
import json

load_dotenv()
client = OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY")
)

##########################################################
######################## Text Gen ########################
##########################################################

def generate_next_line_candidates_list(story_context: str, num_candidates=3, model="gpt-4o-mini") -> list:
    system_prompt = (
    "You are a creative writing assistant."
    "I will provide a story so far, and you will generate multiple possible next lines in JSON format."
    )

    user_prompt = (
    f"Story so far:\n{story_context}\n\n"
    f"Please provide exactly {num_candidates} possible next lines. "
    f"Format them as a JSON list where each item is a dictionary with a 'text' key.\n\n"
    f"Example output:\n"
    f"[\n"
    f'    {{"text": "...option 1..."}},\n'
    f'    {{"text": "...option 2..."}},\n'
    f'    {{"text": "...option 3..."}}\n'
    f"]"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=150
    )

    choices = response.choices
    chat_completion = choices[0]
    content = chat_completion.message.content

    return content

Story = "Once upon a time there was a space cat who was very cute she loved to"

llm_output = generate_next_line_candidates_list(Story)
print(llm_output)

options = json.loads(llm_output)
selected_option = options[1]["text"]
Story += " " + selected_option

print(Story)

###########################################################
######################## Image Gen ########################
###########################################################

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