import os
import openai
from dotenv import load_dotenv
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_next_line_candidates_list(story_context: str, num_candidates=3, model="gpt-4o-mini") -> list:
    system_prompt = (
        "You are a creative writing assistant. "
        "I will provide a story so far, and you will generate a numbered list of possible next lines."
    )

    user_prompt = (
        f"Story so far:\n{story_context}\n\n"
        f"Please provide exactly {num_candidates} possible next lines. Each line should be 1-2 sentences. "
        f"Format them as a list:\n\n"
        f"1) ...\n2) ...\n3) ..."
    )

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=150
    )

    content = response['choices'][0]['message']['content']

    candidates = parse_candidates_from_list(content, num_candidates)

    return candidates

def parse_candidates_from_list(response_text: str, num_candidates: int) -> list:

    pattern = r"\d)\s?(.*)"
    matches = re.findall(pattern, response_text)

# Truncate or fill in if the model returns more/less than desired
    matches = matches[:num_candidates]

    matches = [m.strip() for m in matches if m.strip()]
    return matches