import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

def create_retriever(knowledge_base_path="knowledge_base.md"):
    """
    Creates a retriever from a knowledge base file.
    """
    # Load the knowledge base
    loader = TextLoader(knowledge_base_path)
    documents = loader.load()

    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # The GOOGLE_API_KEY is expected to be set in the environment by the server.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

    # Create the retriever
    retriever = vectorstore.as_retriever()

    return retriever

def create_rag_chain(retriever):
    """
    Creates a RAG chain for question-answering using a Gemini model.
    """
    # The GOOGLE_API_KEY is expected to be set in the environment by the server.

    # Define the prompt template
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    # Define the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

    # Construct the RAG chain
    rag_chain = (
        RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
