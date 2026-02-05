import asyncio
import os
import ssl
from typing import Any, Dict, Optional, List

import certifi
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_chroma import Chroma  # for locally running chroma db
from langchain_core.documents import Document
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

from logger import Colors, log_error, log_header, log_info, log_success, log_warning


load_dotenv()

# configure SSL context to use certifi's certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Initialize HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large-instruct")

vector_store = PineconeVectorStore(
    index_name="documentation-helper-e2e", embedding=embeddings
)

tavily_extract = TavilyExtract()
tavily_map = TavilyMap(max_depth=5, max_breadth=20, max_pages=1000)
tavily_crawl = TavilyCrawl()


async def index_documents_async(docs: List[Document], batch_size: int = 50):
    log_header("VECTOR STORAGE PHASE")
    log_info(
        f"    PineconeVectorStore : Indexing {len(docs)} documents into Pinecone Vector Store",
        Colors.DARKCYAN,
    )

    batches = [docs[i : i + batch_size] for i in range(0, len(docs), batch_size)]
    log_info(
        f"    PineconeVectorStore : Processing {len(batches)} batches of size {batch_size}"
    )

    def add_batch(batch: List[Document], batch_num: int):
        try:
            vector_store.add_documents(batch)  # sync call
            log_success(
                f"    PineconeVectorStore : Successfully indexed batch {batch_num}/{len(batches)} ({len(batch)} documents)."
            )
            return True
        except Exception as e:
            log_error(
                f"    PineconeVectorStore : Error indexing batch {batch_num} - {e}"
            )
            return False

    # Run sync Pinecone insertions in threads
    tasks = [
        asyncio.to_thread(add_batch, batch, i + 1) for i, batch in enumerate(batches)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes
    success_count = sum(1 for result in results if result is True)
    if success_count == len(batches):
        log_success(
            f" All Batches Indexed Successfully. Total Batches: ({success_count}/{len(batches)})"
        )
    else:
        log_warning(
            f" Some Batches Failed to Index. Processed Batches: ({success_count}/{len(batches)})"
        )


async def main():
    """Main entry point for the ingestion module."""
    log_header("DOCUMENTATION HELPER - INGESTION MODULE HAS STARTED")

    log_info(
        "    TavilyCrawl : Starting to Crawl documention from https://python.langchain.com/docs/",
        Colors.PURPLE,
    )
    res = tavily_crawl.invoke(
        {
            "url": "https://python.langchain.com/docs/",
            "max_depth": 5,
            "extract_depths": "advanced",
            # "instructions": "", in case you want to provide custom instructions to the extractor as in what to crawl and what not to
        }
    )

    all_docs = [
        Document(page_content=result["raw_content"], metadata={"source": result["url"]})
        for result in res["results"]
    ]

    log_success(
        f"    TavilyCrawl :Crawling completed. {len(all_docs)} documents found."
    )

    log_header("CHUNKING DOCUMENTS PHASE")
    log_info(
        f"    RecursiveTextSplitter : Processing {len(all_docs)} documents with 4000 chunk size and 200 overlap",
        Colors.YELLOW,
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200,
    )

    splitted_docs = text_splitter.split_documents(all_docs)
    log_success(
        f"    CharacterTextSplitter : Chunking completed. {len(splitted_docs)} chunks created."
    )

    # Process Documents Asynchronously
    await index_documents_async(splitted_docs, batch_size=100)

    log_header("PIPELINE COMPLETED")
    log_success(
        "    Ingestion Pipeline has completed successfully! 🎉",
    )
    log_info("📊 Summary:", Colors.BOLD)
    log_info(f"    Total Documents Crawled: {len(all_docs)}", Colors.BOLD)
    log_info(f"    Total Chunks Created: {len(splitted_docs)}", Colors.BOLD)
    log_info(f"    Vector Store: Pinecone", Colors.BOLD)


if __name__ == "__main__":
    asyncio.run(main())
