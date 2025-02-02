import sqlite3
import uuid

class StoryManager:
    def __init__(self, db_path="story.db"):
        self.db_path = db_path
        self.current_branch = "main"
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""
            CREATE TABLE IF NOT EXISTS story (
                id TEXT PRIMARY KEY,
                content TEXT,
                parent_id TEXT,
                branch_name TEXT,
                user TEXT,
                votes INTEGER DEFAULT 0
            )
            """)
            db.commit()

    def start_story(self, user):
        node_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as db:
            db.execute("INSERT INTO story (id, content, parent_id, branch_name, user, votes) VALUES (?, ?, ?, ?, ?, ?)", 
                       (node_id, "The beginning of the story.", None, "main", user, 0))
            self.current_node_id = node_id
            db.commit()
        return "Story started!"

    def add_candidate_node(self, text, user):
        node_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as db:
            db.execute("INSERT INTO story (id, content, parent_id, branch_name, user, votes) VALUES (?, ?, ?, ?, ?, ?)", 
                       (node_id, text, self.current_node_id, self.current_branch, user, 0))
            db.commit()
        return f"Added candidate: {text}"

    def vote_node(self, node_id):
        with sqlite3.connect(self.db_path) as db:
            db.execute("UPDATE story SET votes = votes + 1 WHERE id = ?", (node_id,))
            db.commit()
        return f"Voted for {node_id[:6]}"

    def get_candidate_nodes(self):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.execute("SELECT id, content, votes FROM story WHERE parent_id = ?", (self.current_node_id,))
            return cursor.fetchall()

    def select_candidate_node(self):
        candidates = self.get_candidate_nodes()
        if not candidates:
            return "No candidate nodes available."
        selected_node = max(candidates, key=lambda x: x[2])  # Select node with highest votes
        self.current_node_id = selected_node[0]
        return f"Selected node {selected_node[0][:6]} with content: {selected_node[1]}"

    def create_branch(self, branch_name):
        with sqlite3.connect(self.db_path) as db:
            parent_id = self.current_node_id
            node_id = str(uuid.uuid4())
            db.execute("INSERT INTO story (id, content, parent_id, branch_name, user, votes) VALUES (?, ?, ?, ?, ?, ?)", 
                       (node_id, f"[Branch {branch_name} begins]", parent_id, branch_name, "system", 0))
            db.commit()
            self.current_node_id = node_id
        return f"Branched into `{branch_name}` from highest voted node!"

    def switch_branch(self, branch_name):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.execute("SELECT 1 FROM story WHERE branch_name = ? LIMIT 1", (branch_name,))
            if cursor.fetchone():
                self.current_branch = branch_name
                self.current_node_id = cursor.fetchone()[0]
                return f"Switched to branch `{branch_name}`."
            return "Branch not found!"

    def generate_graph(self):
        tree = {}
        with sqlite3.connect(self.db_path) as db:
            cursor = db.execute("SELECT id, content, parent_id, votes FROM story WHERE branch_name = ?", (self.current_branch,))
            for node_id, content, parent_id, votes in cursor.fetchall():
                tree[node_id] = (content[:20], parent_id, votes)

        def build_tree(node_id, depth=0):
            if node_id is None:
                return ""
            content, parent_id, votes = tree.get(node_id, ("Unknown", None, 0))
            result = "  " * depth + f"- {content} (Votes: {votes}) ({node_id[:6]})" + "\n"
            for child_id, (child_content, child_parent, child_votes) in tree.items():
                if child_parent == node_id:
                    result += build_tree(child_id, depth + 1)
            return result
        
        root_nodes = [node_id for node_id, (_, parent_id, _) in tree.items() if parent_id is None]
        return "\n".join(build_tree(root) for root in root_nodes)

sm = StoryManager()

sm.start_story("101")

sm.add_candidate_node("yo", "101")

sm.add_candidate_node("yo1", "102")

nodes = sm.get_candidate_nodes()

sm.vote_node(nodes[0][0])

nodes = sm.get_candidate_nodes()

print(nodes)

print(sm.select_candidate_node())

print(sm.add_candidate_node("yo", "101"))

print(sm.generate_graph())