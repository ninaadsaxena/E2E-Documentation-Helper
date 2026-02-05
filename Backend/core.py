from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_pinecone import PineconeVectorStore

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings

load_dotenv()


def run_llm(query: str, chat_history: List[Dict[str, Any]] = []):

        # Initialize embeddings and vector store    
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large-instruct"
    )
    doc_searcher = PineconeVectorStore(
        index_name="documentation-helper-e2e", embedding=embeddings
    )
    chat = ChatOllama(model="gemma3:latest", temperature=0)

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")

    stuff_documents_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt)

    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm = chat, retriever = doc_searcher.as_retriever(), prompt = rephrase_prompt
    )

    qa = create_retrieval_chain(
        retriever=history_aware_retriever, combine_docs_chain=stuff_documents_chain
    )

    result = qa.invoke({"input": query, "chat_history": chat_history})

    new_result = {
        "query": result["input"],
        "result": result["answer"],
        "source_documents": result["context"],
    }

    return new_result


if __name__ == "__main__":

    query = "What is a Langchain Chain?"

    result = run_llm(query)

    print(result["result"])
