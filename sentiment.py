
    
# # #     # Initialize a directed graph
# # #     G = nx.DiGraph()  # DiGraph for directed relationships
    
# # #     # Add nodes (characters)
# # #     for char in characters:
# # #         G.add_node(char)
# # #     relationships = defaultdict(list)

# # #     # Detect relationships based on sentence context
# # #     for sent in doc.sents:
# # #         for char1 in characters:
# # #             for char2 in characters:
# # #                 if char1 != char2:
# # #                     # Infer relationship based on the sentence and context
# # #                     rel = infer_relationship(char1, char2, sent.text)
# # #                     relationships[char1].append((char2, rel))

# # #     # Add edges to the graph
# # #     for char1, relations in relationships.items():
# # #         for char2, rel in relations:
# # #             G.add_edge(char1, char2, relationship=rel)

# # #     return G
# # # G = build_relationship_graph(story_text, characters)

# # # # Draw the directed graph
# # # plt.figure(figsize=(10, 8))
# # # pos = nx.spring_layout(G, seed=42)  # Positioning nodes
# # # nx.draw(G, pos, with_labels=True, node_size=3000, node_color='lightblue', font_size=12, font_weight='bold', arrows=True)

# # # # Annotate edges with relationships
# # # edge_labels = nx.get_edge_attributes(G, "relationship")
# # # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

# # # # Show the graph
# # # plt.title("Character Relationships")
# # # plt.show()

import os
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()
client = OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY")
)

# I am a prompt engineer
def generate_relationships(story_context: str, num_candidates=1, model="gpt-4o-mini") -> list:
    system_prompt = (
        "Your job is to find the relationships between all pairs of characters in a short story." 
        "Analysing each sentence, obtain the different relationships between two characters as \"Character A -> feeling -> Character B\", and nothing more." 
        "The structure of each relationship should strictly start with Character A and end with Character B."
        "Make sure no words come after character B's name, and no words come before character A's. Do not say something like:" 
        "A finds B fun to be around."
        "Instead, say "
        "A -> enjoys being with -> B."
        "This is a strict structure, so please follow the rules no matter what." 

        "Do not add any descriptions, or explanations, as this input will be used to subsequently create a graph of interactions between characters." 

        "Make sure every combination of two-character interactions, where interactions are present, are considered."

        "As the relationship between characters can be complicated, feel free to use more than one sentence to describe their relationship"
    )
    user_prompt = (
        f"Story so far:\n{story_context}\n\n"
        "Please provide the relationship between characters as a structure, in the required format."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9,
        max_tokens=150
    )
    choices = response.choices
    chat_completion = choices[0]
    content = chat_completion.message.content
    print(content)
    return content
story_content = "Alice is deeply in love with Bob, but Bob finds Alice a bit annoying, although he respects her as a good person. Alice often tries to get Bob's attention, but he just doesn't seem interested in her. Alice likes Tracy and finds Tracy very attractive."
generate_relationships(story_content)

import networkx as nx
import matplotlib.pyplot as plt
