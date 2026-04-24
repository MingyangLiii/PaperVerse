from agent.paper_reader import PaperReaderAgent
from agent.utils.load_pdf import Paper
from agent.llm import LLM
from agent.memory_writer import MemoryWriterAgent
import os




def handle_upload(paper_path):
    llm = LLM()
    paper_reader_agent = PaperReaderAgent(llm)
    memory_writer_agent = MemoryWriterAgent(llm)

    print(f"Processing {paper_path}...")
    summaries = paper_reader_agent.read_paper(paper_path) # type: ignore
    memory = memory_writer_agent.write_memory(summaries)
    memory_writer_agent.store_memory(memory)
    print(f"Finished processing {paper_path}.\n")




# def main():
#     llm = LLM()
#     paper_reader_agent = PaperReaderAgent(llm)
#     memory_writer_agent = MemoryWriterAgent(llm)

#     paper_directory = "files"
#     # Get the list of PDF files in the directory
#     paper_files = [f for f in os.listdir(paper_directory) if f.endswith('.pdf')]
#     remove_papers = ["EverMemOS- A Self-Organizing Memory Operating System for Structured Long-Horizon Reasoning.pdf"]

#     paper_files = [f for f in paper_files if f not in remove_papers]
#     for paper_file in paper_files:
#         paper_path = os.path.join(paper_directory, paper_file)

#         print(f"Processing {paper_path}...")
#         summaries = paper_reader_agent.read_paper(paper_path) # type: ignore
        
#         memory = memory_writer_agent.write_memory(summaries)
#         memory_writer_agent.store_memory(memory)
#         print(f"Finished processing {paper_path}.\n")



# if __name__ == "__main__":
#     main()
