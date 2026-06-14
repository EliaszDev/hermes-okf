"""RAG integration example using LangChain and ChromaDB.

Requires: pip install hermes-okf[rag]
"""

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings  # or OpenRouterEmbeddings

from hermes_okf.bundle import OKFBundle

# 1. Load OKF bundle
bundle = OKFBundle("./my_knowledge")

loader = DirectoryLoader(
    str(bundle.root),
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
docs = loader.load()

# 2. Split by markdown headers
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")]
)
splits = []
for doc in docs:
    splits.extend(splitter.split_text(doc.page_content))

# 3. Embed into Chroma
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(),  # swap for your preferred embedding model
    persist_directory="./chroma_okf_db",
)

# 4. Query
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
results = retriever.invoke("What GPU decisions did we make?")
for r in results:
    print(f"---\n{r.page_content[:300]}...\n")
