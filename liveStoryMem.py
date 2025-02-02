from datetime import datetime
from llm_utils import *
# A global or module-level dictionary for active stories (story_id -> story_data)
active_stories = {}

def create_story(story_id: str, starter_line: str, personality: str, user_id: str): # all this info is from discord / we create it
    """
    1) Initialize the in-memory JSON structure
    2) Use LLM to fill in initial metadata (title, genre, tone, style, theme keywords)
    3) Return the populated story data
    """
    story_data = {
        "storyId": story_id,
        "title": "",  # LLM to fill
        "currentStoryText": starter_line,
        "storyMetadata": {
            "genre": "",  # LLM to fill
            "tone": "",   # LLM to fill
            "style": "",  # LLM to fill
            "promptPersonality": personality,
            "themeKeywords": [],  # LLM to fill
            "createdBy": user_id,
            "creationDate": datetime.utcnow().isoformat(),
            "lastUpdated": datetime.utcnow().isoformat()
        },
        "lines": [
            {
                "lineId": "line-001",
                "text": starter_line,
                "addedBy": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "storySummary": "" , # LLM to fill 
        "characters": [],
        "settings": [],
        "storyConfig": {
            "language": "English"
        }
    }

    initial_meta = generate_initial_story_metadata(starter_line)
    print(initial_meta)
    set_story_metadata(story_data, initial_meta)

    story_text = starter_line
    story_summary = generate_story_summary(story_text)
    update_story_summary(story_data, story_summary)

    active_stories[story_id] = story_data

    return story_data


def generate_initial_story_metadata(starter_line: str) -> dict: 
    """
    Use the LLM to propose a title, genre, tone, style, and theme keywords 
    based on the given starter line.
    Returns a dict like:
      {
        "title": "...",
        "genre": "...",
        "tone": "...",
        "style": "...",
        "themeKeywords": ["keyword1", "keyword2", ...]
      }
    """
    prompt = f"""
    The first line of a story is: "{starter_line}"

    Please propose:
    1) A suitable title (short, up to 5 words)
    2) The most fitting genre
    3) An overall tone (e.g., mysterious, whimsical, dark, comedic)
    4) A narrative style (e.g., flowery, concise, action-packed)
    5) A few theme keywords

    Return your answer in valid JSON with exactly the keys:
    "title", "genre", "tone", "style", "themeKeywords"

    Return a dict like:
      {{
        "title": "...",
        "genre": "...",
        "tone": "...",
        "style": "...",
        "themeKeywords": ["keyword1", "keyword2", ...]
      }}
    """
    raw_response = call_llm_api(prompt)
    data = parse_llm_json_response(raw_response)

    return data

def add_new_line_and_update_by_id(story_id: str, new_line: str, added_by: str): # New line is llmed or discord (need logic), we manage story id, added by is from discord
    """
    1) Retrieve the correct story from 'active_stories' by ID
    2) Call 'add_new_line_and_update' to handle LLM-based updates
    3) Update 'active_stories[story_id]' with the new state
    4) Return the updated story data
    """
    story_data = active_stories.get(story_id)
    if not story_data:
        raise ValueError(f"No active story found with ID {story_id}")

    updated_story = add_new_line_and_update(story_data, new_line, added_by)

    active_stories[story_id] = updated_story
    return updated_story

def parse_llm_json_response(llm_response_text: str) -> dict:
    """
    Attempt to parse the LLM's response as JSON. 
    If parsing fails, return an empty dict or handle gracefully.
    """
    import json

    try:
        data = json.loads(llm_response_text)
        return data
    except json.JSONDecodeError:
        # Optionally handle or log the error
        return {}


def set_story_metadata(story_data: dict, extracted_data: dict):
    """
    Given the story data and a metadata dict from generate_initial_story_metadata,
    set the relevant fields in the JSON structure.
    """
    story_data["title"] = extracted_data.get("title", "")
    story_data["storyMetadata"]["genre"] = extracted_data.get("genre", "")
    story_data["storyMetadata"]["tone"] = extracted_data.get("tone", "")
    story_data["storyMetadata"]["style"] = extracted_data.get("style", "")
    story_data["storyMetadata"]["themeKeywords"] = extracted_data.get("themeKeywords", [])
    story_data["storyMetadata"]["lastUpdated"] = datetime.utcnow().isoformat()



def generate_story_summary(full_story_text: str) -> str:
    """
    Ask the LLM for a short summary of the chapter text (1-2 sentences).
    Return just the text string.
    """
    prompt = f"""
    The following text is the content of the story:
    "{full_story_text}"

    Please provide a concise 1-2 sentence summary of this chapter.
    Return just the summary text (no JSON needed).
    """
    raw_response = call_llm_api(prompt)
  
    return raw_response

def update_story_summary(story_data: dict, new_summary: str):
    """
    Set or replace the storySummary.
    """
    story_data["storySummary"] = new_summary
    story_data["storyMetadata"]["lastUpdated"] = datetime.utcnow().isoformat()

def add_new_line_and_update(story_data: dict, new_line: str, added_by: str):
    """
    1) Add the new line to story_data["lines"]
    2) Call LLM to discover new characters/settings
    3) Update the entire story summary
    """
    # 1. Append new line
    line_id = f"line-{len(story_data['lines'])+1:03d}"
    line_entry = {
        "lineId": line_id,
        "text": new_line,
        "addedBy": added_by,
        "timestamp": datetime.utcnow().isoformat()
    }
    story_data["lines"].append(line_entry)

    # Also update the overall text
    story_data["currentStoryText"] += " " + new_line

    # 2. LLM prompt to extract new characters/settings from the latest line
    prompt_extract = f"""
    The story so far is:
    {story_data['currentStoryText']}

    The latest line is: "{new_line}"

    If any new characters have been introduced or revealed with more details, 
    please include them in JSON under the key "newCharacters". 
    Each character should have:
    - "name"
    - "description"
    - "status"
    - "traits" (an array)
    - (optionally) "opinionsOf" (an array of objects representing opinions about specific characters):
        [
        {{
            "characterName": "...",
            "opinionText": "...",
            "trustLevel": 0
        }},
        ...
        ]

    If any new settings (locations) have been introduced or revealed, 
    please include them in JSON under the key "newSettings", each with:
    - "locationName"
    - "description"
    - "keyDetails" (an array of strings)

    Return valid JSON with these exact top-level keys if relevant:

    "newCharacters": [
    {{
        "name": "...",
        "description": "...",
        "status": "...",
        "traits": [],
        "opinionsOf": [
        {{
            "characterName": "...",
            "opinionText": "...",
            "trustLevel": 0
        }},
        ...
        ]
    }},
    ...
    ],
    "newSettings": [
    {{
        "locationName": "...",
        "description": "...",
        "keyDetails": []
    }},
    ...
    ]

    Omit any sections (or keys) that are not applicable.
    """

    raw_response = call_llm_api(prompt_extract)
    extracted_data = parse_llm_json_response(raw_response)

    # Update characters, settings
    add_characters(story_data, extracted_data.get("newCharacters", []))
    add_settings(story_data, extracted_data.get("newSettings", []))

    # 3. Update the summary for the entire story
    new_summary = generate_story_summary(story_data["currentStoryText"])
    update_story_summary(story_data, new_summary)

    return story_data


def add_characters(story_data: dict, characters: list):
    """
    Given a list of character dicts like:
    [
      {"name": "X", "description": "desc", "status": "Active", "traits": [...]},
      ...
    ]
    Append them to story_data["characters"] if they're not already present.
    """
    existing_characters = story_data.get("characters", [])

    for new_char in characters:
        # Check for duplicates by name (or handle it differently if multiple chars can share name)
        if not any(c["name"] == new_char["name"] for c in existing_characters):
            existing_characters.append(new_char)

    story_data["characters"] = existing_characters

    story_data["storyMetadata"]["lastUpdated"] = datetime.utcnow().isoformat()



def add_settings(story_data: dict, settings: list):
    """
    Given a list of setting dicts like:
    [
      {
        "locationName": "The Starbound Voyager",
        "description": "A deep-space exploration vessel",
        "keyDetails": ["cryo bays", "control room"]
      }
    ]
    Append them if not present.
    """
    existing_settings = story_data.get("settings", [])

    for new_set in settings:
        if not any(s["locationName"] == new_set["locationName"] for s in existing_settings):
            existing_settings.append(new_set)

    story_data["settings"] = existing_settings

    story_data["storyMetadata"]["lastUpdated"] = datetime.utcnow().isoformat()


def get_story(story_id: str):
    return active_stories.get(story_id)

def finalize_story(story_id: str) -> dict:

    story_data = active_stories[story_id]

    prompt = f"""
    The completed story is: "{story_data["currentStoryText"]}"

    Please propose:
    1) A suitable title (short, up to 5 words)
    2) The most fitting genre
    3) An overall tone (e.g., mysterious, whimsical, dark, comedic)
    4) A narrative style (e.g., flowery, concise, action-packed)
    5) A few theme keywords

    Return your answer in valid JSON with exactly the keys:
    "title", "genre", "tone", "style", "themeKeywords"

    Return a dict like:
      {{
        "title": "...",
        "genre": "...",
        "tone": "...",
        "style": "...",
        "themeKeywords": ["keyword1", "keyword2", ...]
      }}
    """
    raw_response = call_llm_api(prompt)
    data = parse_llm_json_response(raw_response)

    set_story_metadata(story_data, data)

    story_summary = generate_story_summary(story_data["currentStoryText"])
    update_story_summary(story_data, story_summary)

    story_data = active_stories.pop(story_id, None)
    return story_data

# Example use
#create_story(1234, "Once upon time there was a very sleep university student who wanted to", "desolate", "me")
#add_new_line_and_update_by_id(1234, accept_winning_line(generate_next_line_candidates_list(active_stories[1234]["currentStoryText"],personality=active_stories[1234]["storyMetadata"]["promptPersonality"]), 0), "llm")
#print(active_stories[1234]["currentStoryText"])
#x = input()
#add_new_line_and_update_by_id(1234, x, "me")
#add_new_line_and_update_by_id(1234, accept_winning_line(generate_next_line_candidates_list(active_stories[1234]["currentStoryText"],personality=active_stories[1234]["storyMetadata"]["promptPersonality"]), 0), "llm")
#complete_story = finalize_story(1234)
#print(complete_story["currentStoryText"])
#print(complete_story)