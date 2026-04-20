import pymupdf


class Paper:
    def __init__(self, path):
        doc = pymupdf.open(path)

        self.title = doc.metadata.get('title', '') # type: ignore
        self.authors = doc.metadata.get('author', '') # type: ignore

        self.table_of_contents = [ls[1] for ls in doc.get_toc()]
        self.pages = [page.get_text() for page in doc]
    

    def __str__(self):
        return self.get_text()
    
    def get_pages(self):
        return self.pages
    
    def get_table_of_contents(self):
        return self.table_of_contents
    
    def get_text(self):
        full_context = ""
        for page in self.pages:
            full_context += str(page) + " "
        return full_context

