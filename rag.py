from pathlib import Path
from dotenv import load_dotenv
from uuid import uuid4

from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = None
vector_store = None

LLM_MODEL = 'llama-3.1-8b-instant'
CHUNK_SIZE = 1000
COLLECTION_NAME = "news"
EMBEDED_MODEL = "BAAI/bge-small-en-v1.5"
VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"

def initilize_components():
    global llm, vector_store

    if llm is None:
        llm = ChatGroq(model=LLM_MODEL, temperature=0.9, max_tokens=500)

    if vector_store is None:
        ef = HuggingFaceEmbeddings(
            model_name = EMBEDED_MODEL,
            model_kwargs = { "trust_remote_code" : True }
        ) 
        vector_store = Chroma(
            collection_name = COLLECTION_NAME,
            persist_directory= str(VECTORSTORE_DIR),
            embedding_function=ef
        )

# store url content to DB
def procress_url(urls):

    # initialize components
    yield 'Initialize components'
    initilize_components()

    yield 'Resetting Vector Store'
    vector_store.reset_collection()

    # Load data
    yield 'Load data'
    loader = UnstructuredURLLoader(urls)
    data = loader.load()

    # Split Text 
    yield 'Split Text'
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        separators=["\n\n", "\n", ".", " "]
    )

    docs = text_splitter.split_documents(data)

    # add docs to vector db
    yield 'Add docs to vector db'
    uuids = [str(uuid4()) for _ in range(len(docs))]
    vector_store.add_documents(docs, ids=uuids)

    yield 'Done Adding Docs to Vector Database...'

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate_answer(query):
    if not vector_store:
        raise RuntimeError("Vector DB is not initialized")

    retriever = vector_store.as_retriever()   

    prompt = ChatPromptTemplate.from_template(
        """Answer the question using the provided context.
        Also include sources at the end.

        Context:
        {context}

        Question:
        {input}

        Answer (include sources):"""
    )

    chain = (
        {
            "context": retriever | format_docs,
            "input": lambda x: x
        }
        | prompt
        | llm
    )

    result = chain.invoke(query)

     # sources extraction
    docs = retriever.invoke(query)
    sources = list(set(doc.metadata.get("source", "") for doc in docs))

    return result.content, ", ".join(sources)


if __name__ == "__main__":
    urls = ['https://news.yahoo.com/'] 

    procress_url(urls)

    # # Retrival 
    # results = vector_store.similarity_search(
    #     "You will be shown some punishments that are inflicted on a girl.",
    #     k=2
    # ) 

    # print(results)

    ## give chunck to LLM to genereate answer
    answer , sources = generate_answer("Did preeti enjoyed her punishment? ")
    print(f"Answer: {answer}")
    print(f"Sources: {sources}")
    