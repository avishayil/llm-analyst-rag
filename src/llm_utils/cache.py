import logging
import os

from langchain_community.cache import RedisSemanticCache
from langchain_core.outputs.generation import Generation
from scipy.spatial.distance import cosine

from src.llm_utils.constants import BEDROCK_EMBEDDINGS_MODEL_ID

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, embeddings_model, similarity_threshold=0.2):
        """
        Initialize the semantic cache using Redis and the provided embeddings model.
        :param embeddings_model: The embeddings model for generating vectors
        :param similarity_threshold: Threshold for cosine similarity
        """
        self.cache = RedisSemanticCache(
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
            embedding=embeddings_model,
            score_threshold=similarity_threshold,
        )
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def normalize_cache_key(cache_key: str) -> str:
        """
        Normalize the cache_key and hash it for use as a cache key.
        :param cache_key: The raw cache_key
        :return: A hashed string derived from the normalized cache_key
        """
        normalized = cache_key.strip().replace(" ", "_").lower()
        # Use SHA256 to generate a fixed-length hash
        return normalized

    @staticmethod
    def _calculate_similarity(vector_a, vector_b):
        """
        Calculate cosine similarity between two vectors.
        :param vector_a: First vector
        :param vector_b: Second vector
        :return: Cosine similarity score
        """
        return 1 - cosine(vector_a, vector_b)

    def lookup(self, cache_key: str, llm_string: str = BEDROCK_EMBEDDINGS_MODEL_ID):
        """
        Query the cache using a normalized cache_key.
        :param cache_key: The cache key
        :param llm_string: The LLM configuration or version string
        :return: The cached response if available, else None
        """
        normalized_cache_key = self.normalize_cache_key(cache_key)
        logger.info(
            f"Querying cache with cache_key: {normalized_cache_key} and llm_string: {llm_string}"
        )
        try:
            cached_response = self.cache.lookup(
                prompt=normalized_cache_key, llm_string=llm_string
            )
            if cached_response:
                logger.info("Cache hit: Returning cached response")
            else:
                logger.info("Cache miss: No matching response found")
            return cached_response
        except Exception as e:
            logger.error(f"Error during cache lookup: {e}", exc_info=True)
            return None

    def update(self, cache_key: str, llm_string: str, value: str):
        """
        Update the cache with a new response.
        :param cache_key: The cache_key
        :param llm_string: The LLM configuration or version string
        :param value: The response to cache
        """
        normalized_cache_key = self.normalize_cache_key(cache_key)
        cache_key = normalized_cache_key
        logger.info(
            f"Updating cache with cache_key: {normalized_cache_key} and llm_string: {llm_string}"
        )
        try:
            self.cache.update(
                prompt=cache_key,
                llm_string=llm_string,
                return_val=[Generation(text=value)],
            )
            logger.info("Cache updated successfully")
        except Exception as e:
            logger.error(f"Error updating cache: {e}", exc_info=True)
