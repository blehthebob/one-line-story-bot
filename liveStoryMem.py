from datetime import datetime
from llm_utils import *
from imgToVid import *
import requests

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

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

def save_graph(story_id):
    folder_path = f"Stories/{story_id}/Graphs"
    os.makedirs(folder_path, exist_ok=True)

    existing_files = [f for f in os.listdir(folder_path) if f.endswith(".png")]

    next_number = len(existing_files) + 1
    file_name = f"graph_{next_number}.png"
    file_path = os.path.join(folder_path, file_name)

    plt.savefig(file_path, format="png", dpi=300)
    #print(f"Graph saved as: {file_path}")

#function to create graph
def create_graph(characters, story_id):
    print(len(characters))
    if len(characters)>0:
        # Create a MultiDiGraph (allows multiple edges)
        G = nx.MultiDiGraph()

        # Initialize the edge_offsets dictionary
        edge_offsets = {}

        # Add nodes and edges based on opinions
        for character in characters:
            for opinion in character["opinionsOf"]:
                source = character["name"]
                target = opinion["characterName"]
                opinion_text = opinion["opinionText"]
                trust_level = opinion["trustLevel"]
                edge_label = f"{opinion_text} - {trust_level}"

                # Add the edge from source to target if not already added
                if not G.has_edge(source, target):
                    G.add_edge(source, target, label=edge_label)

                # Check if the target has an opinion about the source
                reverse_opinion = next((op for op in characters if op["name"] == target), None)
                if reverse_opinion:
                    reverse_opinion = next((o for o in reverse_opinion["opinionsOf"] if o["characterName"] == source), None)
                    if reverse_opinion:
                        reverse_opinion_text = reverse_opinion["opinionText"]
                        reverse_trust_level = reverse_opinion["trustLevel"]
                        reverse_edge_label = f"{reverse_opinion_text} - {reverse_trust_level}"

                        # Add reverse edge only if not already added
                        if not G.has_edge(target, source):
                            G.add_edge(target, source, label=reverse_edge_label)

        # Draw the graph with a slight offset for separation
        pos = nx.spring_layout(G, seed=42) 

        # Create a figure and axis for drawing
        plt.figure(figsize=(10, 6))
        node_size = 2000
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=node_size)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

        # Draw the edges and adjust positions for each edge
        for u, v, key in G.edges(keys=True):
            edge_data = G[u][v][key]
            label = edge_data['label']

            # Initialize the offset for this edge if not already set
            if (u, v) not in edge_offsets:
                edge_offsets[(u, v)] = 0.9  # Set the initial offset to 3

            # Increment the offset for subsequent edges between the same pair of nodes
            else:
                edge_offsets[(u, v)] += 2  # Increase by 2 for each new edge

            # Adjust the position of the edge slightly based on the offset
            offset = edge_offsets[(u, v)]
            pos_u = np.array(pos[u])
            pos_v = np.array(pos[v])
            
            edge_vector = pos_v - pos_u
            edge_vector /= np.linalg.norm(edge_vector) 
            edge_vector *= offset

            # Draw the edges with the adjusted positions
            nx.draw_networkx_edges(G, pos, node_size = node_size, edgelist=[(u, v)], width=1, alpha=0.7, edge_color='gray', arrows=True, arrowsize = 25, connectionstyle=f"arc3,rad={0.1 * offset}")

            # Calculate and place the edge labels slightly offset from the edge path
            midpoint = (np.array(pos_u) + np.array(pos_v)) / 2  

            # Apply different offsets based on the edge direction
            if (u, v) in G.edges():
                label_offset = 0.05  
            else:
                label_offset = -0.05  

            label_position = midpoint + np.array([label_offset, label_offset])

            # Draw the edge labels (opinion text and trust level) without modifying node positions
            nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v, key): label}, font_size=8, verticalalignment="center", horizontalalignment="center", label_pos=0.5,connectionstyle=f"arc3,rad={0.1 * offset}")


        # Title and show the plot
        plt.title("Character Relationships Graph")
        plt.axis('off')  # Hide the axes for better visualization

        save_graph(story_id)


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
    story_data["currentStoryText"] += " " + new_line.rstrip() + ("." if new_line[-1] != "." else "")

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
    story_id = story_data["story_Id"]
    create_graph(existing_characters, story_id)

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

    story_id = story_data["story_Id"]

    ##final_image_url = generate_final_image(build_dalle_prompt(story_data)) ## Comment to save money
    ##imgName = story_data["title"]## Comment to save money
    ##story_id = story_data["story_Id"]
    ##save_image(final_image_url, folder=f"Stories/{story_id}" filename=f"{imgName}.png") ## Comment to save money

    save_story_data(story_data, folder=f"Stories/{story_id}")

    images_to_video(f"Stories/{story_id}/Graphs", f"Stories/{story_id}/ConnectionsTimeline.mp4")

    return story_data

def save_story_data(story_data, folder="Stories"):
    title = story_data["title"]
    filename=f"{title}.json"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=4) 

    print(f"Story data saved to {file_path}")

    return story_data

def save_image(image_url, folder="Stories", filename="generated_image.png"):
    image_data = requests.get(image_url).content
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, filename)
    # Write the content to a file
    with open(file_path, "wb") as file:
        file.write(image_data)
    print(f"Saved image to {filename}")

def build_dalle_prompt(story_data: dict) -> str:
    metadata = story_data["storyMetadata"]
    title = story_data["title"]
    genre = metadata.get("genre", "")
    tone = metadata.get("tone", "")
    style = metadata.get("style", "")
    keywords = ", ".join(metadata.get("themeKeywords", []))
    
    # Summarize characters
    character_summaries = []
    for char in story_data.get("characters", []):
        name = char.get("name", "Unknown Character")
        traits = ", ".join(char.get("traits", []))
        desc = f"{name} ({traits})" if traits else name
        character_summaries.append(desc)
    characters_str = "\n- " + "\n- ".join(character_summaries) if character_summaries else "None"
    
    # Summarize settings
    setting_summaries = []
    for setting in story_data.get("settings", []):
        location = setting.get("locationName", "Unknown Location")
        set_desc = setting.get("description", "")
        setting_summaries.append(f"{location}: {set_desc}")
    settings_str = "\n".join(setting_summaries) if setting_summaries else "No specific setting"

    # Possibly a truncated or summarized version of the story text
    story_desc = story_data.get("storySummary", "") 
    
    prompt = f"""
Create an illustration inspired by the following story and its metadata:

Title: {title}
Genre: {genre}
Tone: {tone}
Art Style: {style}
Theme Keywords: {keywords}

Story Description:
"{story_desc}"

Key Characters:{characters_str}

Setting:
{settings_str}

Art Direction:
- Reflect the story’s {genre} genre and maintain a {tone} atmosphere.
- Incorporate visual elements that hint at {keywords}, ensuring a cohesive look.
- Depict the characters and setting in a scene representing the central conflict or theme.
- Aim for a {style} style (or related visual approach).
- Emphasize the emotional essence that fits the story's tone and theme.

Color Palette & Composition:
- Suggest a palette that conveys {tone} vibe.
- Composition can be cinematic, minimalist, or surreal as needed.

Please produce a image with enough detail to capture the story’s essence and characters in a single, cohesive scene.
"""
    return prompt.strip()


    
# Example use
# story_id = 1234
# create_story(story_id, "Once upon time there was a very sleep university student who wanted to", "desolate", "me")
# add_new_line_and_update_by_id(story_id, accept_winning_line(generate_next_line_candidates_list(active_stories[story_id]["currentStoryText"],personality=active_stories[story_id]["storyMetadata"]["promptPersonality"]), 0), "llm")
# print(active_stories[story_id]["currentStoryText"])
# x = input()
# add_new_line_and_update_by_id(story_id, x, "me")
# add_new_line_and_update_by_id(story_id, accept_winning_line(generate_final_line_candidates_list(active_stories[story_id]["currentStoryText"], personality=active_stories[story_id]["storyMetadata"]["promptPersonality"]), 0 ), "llm")
# complete_story = finalize_story(story_id)
# print(complete_story["currentStoryText"])
# print(complete_story)