from langchain_community.document_loaders import WebBaseLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.globals import set_llm_cache
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.caches import InMemoryCache
from langchain_core.prompts import PromptTemplate

from bs4 import BeautifulSoup
import requests

BASE_URL = "https://www.noobscience.in"
DEFAULT_PROMPT_TEMPLATE = """Answer the following question to a user {question} 
with the following context {context}"""


def parse_blogurls():
    soup = BeautifulSoup(requests.get(BASE_URL + "/blog").content, "html.parser")
    urls = []

    for a_tag in soup.find_all("a", class_="underline"):
        urls.append(a_tag["href"])

    return urls


def get_blog_documents(urls):
    loader = WebBaseLoader(web_paths=urls)
    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    return docs


class CustomGeminiRAG:
    def __init__(self, google_api_key, prompt=DEFAULT_PROMPT_TEMPLATE):
        self.urls = [(BASE_URL + a) for a in parse_blogurls()[1:]]
        self.docs = get_blog_documents(self.urls)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", google_api_key=google_api_key
        )
        self.vector_store = self.prepare_vector_store()
        self.llm = GoogleGenerativeAI(model="gemini-2.0-flash", api_key=google_api_key)
        set_llm_cache(InMemoryCache())
        self.prompt = PromptTemplate.from_template(prompt)
        pass

    def prepare_vector_store(self):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        all_splits = text_splitter.split_documents(self.docs)
        vector_store = InMemoryVectorStore(self.embeddings)
        vector_store.add_documents(documents=all_splits)

        return vector_store

    def search(self, query):
        results = self.vector_store.similarity_search_with_score(query=query, k=1)
        return [a[0] for a in results if a[1] > 0.5]

    def ask(self, question: str) -> str:
        rel_docs = self.search(question)
        context = "\n\n".join(doc.page_content for doc in rel_docs)
        print(
            f'Using content of {",".join([doc.metadata['source'] for doc in rel_docs])} '
        )
        final_prompt = self.prompt.invoke({"question": question, "context": context})
        response = self.llm.invoke(final_prompt)

        return response
