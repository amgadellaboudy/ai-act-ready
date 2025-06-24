from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

print('Reading pdf...')
reader = PdfReader("EU_AI_ACT.pdf")
full_text = "\n".join(p.extract_text() for p in reader.pages)

print('Chunking Text...')
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = splitter.split_text(full_text)
docs = [Document(page_content=t) for t in texts]

print('Embedding and saving text...')
emb = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(docs, emb)

# Persist FAISS index to disk (recommended)
faiss_dir = "faiss_index"
vectorstore.save_local(faiss_dir)

