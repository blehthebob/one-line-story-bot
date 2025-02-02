from llm_utils import *

def load_story_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        story_data = json.load(f)  # Load JSON data into a Python dictionary
    return story_data

file_path = "Stories" + os.sep + "EmbracingExhaustion.json"  # Path to your JSON file
story_data = load_story_data(file_path)


def evaluate_story(story_data: dict) -> dict:
    metadata = story_data.get("storyMetadata", {})
    lines = story_data.get("lines", [])
    characters = story_data.get("characters", [])
    settings = story_data.get("settings", [])
    story_text = story_data.get("currentStoryText", "")

    data = produce_score(story_data)
    
    plot_cohesion_score = data.get("plotCohesion", 0)
    creativity_score = data.get("creativity", 0)
    characters_score = data.get("characters", 0)
    setting_score = data.get("settingAtmosphere", 0)
    tone_style_score = data.get("toneStyleAlignment", 0)
    completeness_score = data.get("completeness", 0)
    
    score_sum = (plot_cohesion_score + creativity_score + characters_score
                 + setting_score + tone_style_score + completeness_score)

    rank = score_to_rank(score_sum)

    print(rank)
    print(data)
    
    return {
        "scoreDetails": {
            "plotCohesion": plot_cohesion_score,
            "creativity": creativity_score,
            "characters": characters_score,
            "settingAtmosphere": setting_score,
            "toneStyleAlignment": tone_style_score,
            "completeness": completeness_score,
        },
        "totalScore": score_sum,
        "rank": rank
    }

def produce_score(story_data):
    prompt = f"""
        You are an evaluator of completed short stories.  
        I will provide you with the final story data in JSON format, including metadata (genre, tone, style, etc.), the full text of the story, its characters, and settings.

        ### Task:
        1. Read and analyze all of the provided story data carefully.
        2. Score the story on **six** categories, each on a **0–10 scale** (0 = extremely poor, 10 = exceptional):
        - **plotCohesion**: Do the story lines connect logically? Is there a sense of progression or conflict/resolution?
        - **creativity**: How original or imaginative is the premise, setting, and execution?
        - **characters**: Are the characters well-defined, interesting, and appropriate to the story’s conflict/genre?
        - **settingAtmosphere**: Does the story effectively establish and use the setting (including mood/tone match)?
        - **toneStyleAlignment**: Does the writing style (e.g., “concise,” “flowery”) and overall tone match the story’s metadata (genre, tone) and maintain consistency?
        - **completeness**: Does the story feel finished or suitably concluded?

        5. Provide your results **only** in valid JSON with exactly these keys:
        {{ "plotCohesion": 0, "creativity": 0, "characters": 0, "settingAtmosphere": 0, "toneStyleAlignment": 0, "completeness": 0}}

        - Each of the six keys is an **integer** 0–10.

        No additional commentary. No code fences.

        Here is the story data to evaluate: {story_data}

        Remember, respond in **valid JSON** with the exact 6 keys described. No extra text or formatting.
        """
    raw_data = call_llm_api(prompt)
    data = json.loads(raw_data)

    return data

def score_to_rank(score: int) -> str:
    if        score <= 10:    return "E"
    elif 10 < score <= 20:    return "D"
    elif 20 < score <= 30:    return "C"
    elif 30 < score <= 40:    return "B"
    elif 40 < score <= 50:    return "A"
    elif 50 < score <= 55:    return "S"
    elif 55 < score <= 59:    return "SS"
    else:                     return "BEST STORY OF ALL TIME"


evaluate_story(story_data)