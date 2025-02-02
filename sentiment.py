import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Example input JSON data (same as before)
characters = [
    {
        "name": "Alice", 
        "description": "A curious explorer.",
        "status": "Active", 
        "traits": ["Brave", "Inquisitive"],
        "opinionsOf": [
            {
                "characterName": "Bob", 
                "opinionText": "Friendly and loyal.", 
                "trustLevel": 8
            },
            {
                "characterName": "Charlie", 
                "opinionText": "A bit too secretive.", 
                "trustLevel": 5
            }
        ]
    },
    {
        "name": "Bob", 
        "description": "A loyal friend.", 
        "status": "Active", 
        "traits": ["Loyal", "Honest"],
        "opinionsOf": [
            {
                "characterName": "Alice", 
                "opinionText": "Adventurous and smart.", 
                "trustLevel": 9
            },
            {
                "characterName": "Charlie", 
                "opinionText": "Mysterious but trustworthy.", 
                "trustLevel": 7
            }
        ]
    },
    {
        "name": "Charlie", 
        "description": "A quiet strategist.",
        "status": "Inactive", 
        "traits": ["Strategic", "Reserved"],
        "opinionsOf": [
            {
                "characterName": "Alice", 
                "opinionText": "A bit too loud, but capable.", 
                "trustLevel": 6
            },
            {
                "characterName": "Bob", 
                "opinionText": "Reliable and practical.", 
                "trustLevel": 8
            }
        ]
    }
]

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
pos = nx.spring_layout(G, seed=42)  # Positioning for the nodes
adjusted_pos = pos.copy()  # Create a copy of the positions to adjust edge labels only

# Create a figure and axis for drawing
plt.figure(figsize=(10, 6))

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=2000)
nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

# Draw the edges and adjust positions for each edge
for u, v, key in G.edges(keys=True):
    edge_data = G[u][v][key]
    label = edge_data['label']

    # Initialize the offset for this edge if not already set
    if (u, v) not in edge_offsets:
        edge_offsets[(u, v)] = 3  # Set the initial offset to 3

    # Increment the offset for subsequent edges between the same pair of nodes
    else:
        edge_offsets[(u, v)] += 2  # Increase by 2 for each new edge

    # Adjust the position of the edge slightly based on the offset
    offset = edge_offsets[(u, v)]
    pos_u = np.array(pos[u])
    pos_v = np.array(pos[v])
    
    edge_vector = pos_v - pos_u
    edge_vector /= np.linalg.norm(edge_vector)  # Normalize
    edge_vector *= offset

    adjusted_pos_u = pos_u + 0.1
    adjusted_pos_v = pos_v + 0.1
    adjusted_pos[u] = adjusted_pos_u
    adjusted_pos[v] = adjusted_pos_v
    # Draw the edges with the adjusted positions
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=2, alpha=0.7, edge_color='gray', arrows=True, connectionstyle=f"arc3,rad={0.1 * offset}")

    # Calculate and place the edge labels slightly offset from the edge path
    midpoint = (np.array(pos_u) + np.array(pos_v)) / 2  # Use the original node positions

    # Apply different offsets based on the edge direction
    if (u, v) in G.edges():
        label_offset = 0.05  # Forward edge label offset
    else:
        label_offset = -0.05  # Reverse edge label offset

    label_position = midpoint + np.array([label_offset, label_offset])

    # Draw the edge labels (opinion text and trust level) without modifying node positions
    nx.draw_networkx_edge_labels(G, adjusted_pos, edge_labels={(u, v, key): label}, font_size=8, verticalalignment="center", horizontalalignment="center", label_pos=0.5)

# Title and show the plot
plt.title("Character Relationships Graph (Multigraph with Separated Arrows and Edge Labels)")
plt.axis('off')  # Hide the axes for better visualization
plt.show()
