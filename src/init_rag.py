from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


loader = PyMuPDFLoader(file_path="Synthetic-Bank-Policies-Data.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=20)
docs = splitter.split_documents(documents)
emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
db = FAISS.from_documents(docs, embedding=emb)
db.save_local("faiss_store")
