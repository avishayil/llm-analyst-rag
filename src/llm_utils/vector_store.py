import logging
from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_redis import RedisVectorStore

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages a vector store using RedisVectorStore for saving and retrieving embedded documents.
    """

    def __init__(self, embeddings: Embeddings) -> None:
        """
        Initializes the vector store with Redis configuration retrieved from AWS Secrets Manager.

        Args:
            embeddings (Embeddings): The embeddings model to use for vector storage.
        """

        self.redis_host = "localhost"
        self.redis_port = 6379  # Default Redis port is 6379
        self.redis_index = "cve_index"

        self.store = RedisVectorStore(
            embeddings=embeddings,
            redis_url=f"redis://{self.redis_host}:{self.redis_port}",
            index_name=self.redis_index,
        )

    def save(self, documents: List[Document]) -> VectorStoreRetriever:
        """
        Saves a list of documents with their embeddings into the vector store and returns a retriever.

        Args:
            documents (List[Document]): A list of documents to save in the vector store.

        Returns:
            VectorStoreRetriever: A retriever configured with specific search parameters.

        Raises:
            Exception: If an error occurs during document storage.
        """
        try:
            self.store.add_documents(documents=documents)
            logger.info("Successfully loaded documents to the vector store.")
        except Exception as e:
            logger.error(f"Error loading documents to the vector store: {e}")
            raise

        return self.store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 50},
        )

    def load(self) -> VectorStoreRetriever:
        """
        Loads the vector store as a retriever with predefined search parameters.

        Returns:
            VectorStoreRetriever: A retriever configured for vector-based document search.
        """
        return self.store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 50},
        )
