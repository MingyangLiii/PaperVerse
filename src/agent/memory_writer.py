from agent.llm import LLM
from typing import Dict, List
import json
import os


class MemoryWriterAgent:
    def __init__(self, llm: LLM, path: str="kg/knowledge_graph.json"):
        self.llm = llm
        self.path = path

    def system_prompt(self) -> str:
        return """
        You are a Knowledge Graph Extraction Agent. Your task is to transform text summaries into a structured Knowledge Graph.
        
        ### Extraction Rules:
        1. **Nodes**: Identify key entities (systems, phases, benchmarks, components).
        2. **Edges**: Identify the relationships between those entities.
        3. **Consistency**: Ensure the 'from' and 'to' fields in edges exactly match the 'name' of a node.
        
        ### Output Format:
        Return ONLY a valid JSON list containing two types of objects:
        
        - Node: {"name": "Entity Name", "type": "node", "content": "Summary of entity"}
        - Edge: {"name": "Relationship Label", "type": "edge", "from": "Node A", "to": "Node B", "content": "Relationship description"}
        
        Do not include any preamble, markdown formatting (like ```json), or postscript.
        """


    def write_memory(self, memory: Dict) -> List[Dict]:
        """
        Processes the input memory summary and returns a list of JSON-style dictionaries.
        """
        input_text = json.dumps(memory)
        
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": f"Extract the knowledge graph from this summary: {input_text}"}
        ]
        
        response = self.llm.chat(messages)
        
        try:
            clean_json = response.strip().replace("```json", "").replace("```", "") # type: ignore
            graph_data = json.loads(clean_json)
            return graph_data
        except json.JSONDecodeError:
            # Fallback/Error handling if LLM output is malformed
            print("Error: LLM output was not valid JSON.")
            return []
        

    def store_memory(self, memory: List[Dict]):
        existing_data = []
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = []

        if isinstance(memory, list):
            existing_data.extend(memory)
        else:
            existing_data.append(memory)

        with open(self.path, "w") as f:
            json.dump(existing_data, f, indent=2)

