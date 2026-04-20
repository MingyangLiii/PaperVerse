from agent.utils.load_pdf import Paper
from agent.llm import LLM

from typing import Dict, List
import json



class PaperReaderAgent:
    def __init__(self, llm: LLM):
        self.llm = llm


    def system_prompt(self, toc: List[str]) -> str:
        toc_str = "\n".join([f"- {item}" for item in toc])
        return (
            "### ROLE\n"
            "You are a precise Academic Data Extraction Agent. You are processing a research paper "
            "one page at a time. Your goal is to map content from the current page to specific "
            "headings in the provided Table of Contents (ToC).\n\n"
            "### REFERENCE TABLE OF CONTENTS (ToC)\n"
            f"{toc_str}\n\n"
            "### CONSTRAINTS\n"
            "1. Output format: Return ONLY a raw JSON dictionary. Do not include markdown code blocks (```json), "
            "preambles, or conversational text.\n"
            "2. Key Strictness: Every key in your dictionary MUST match an entry from the ToC provided above exactly.\n"
            "3. Page Isolation: Only summarize information physically present on the current page. If a section "
            "is mentioned but the text isn't on this page, do not include it.\n"
            "4. Boundary Handling: If a page contains the end of Section A and the start of Section B, "
            "your dictionary must contain both keys with their respective page-specific summaries.\n"
            "5. Summary Style: Use technical, information-dense prose. Focus on specific methodologies, "
            "variables, results, and citations present on the page.\n"
            "6. Empty Returns: If the page contains no relevant section content (e.g., a full-page diagram or "
            "references not in the ToC), return an empty dictionary: {}.\n\n"
            "### EXPECTED OUTPUT EXAMPLE\n"
            "{\"1. Introduction\": \"The page outlines the scaling laws of LLMs and defines the 'EverMem' architecture...\", "
            "\"2. Related Work\": \"The author critiques current RAG implementations, citing latency issues in...\"}"
        )


    def read_paper(self, paper_path: str, debug: bool = False) -> Dict:
        paper = Paper(paper_path)
        toc = paper.table_of_contents

        prompt = self.system_prompt(toc)
        pages = paper.get_pages()

        summaries = {}

        for index in range(0, len(pages)-1, 2):

            if index ==len(pages)-1:
                page = pages[index] # type: ignore
            else:
                page = pages[index] + "\n" + pages[index+1] # type: ignore

            messages = [{"role": "system", "content": prompt},
                        {"role": "user", "content": page}]
            response = self.llm.chat(messages)


            if debug:
                print("LLM Response:", response) # Debugging output

            try:
                clean_json = response.strip().replace("```json", "").replace("```", "") # type: ignore
                page_summary = json.loads(clean_json) # type: ignore
                summaries.update(page_summary) # type: ignore
            except json.JSONDecodeError:
                continue

        return summaries



