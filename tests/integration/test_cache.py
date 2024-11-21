import pytest
from langchain_core.language_models.llms import Generation

from src.llm_utils.cache import Cache
from src.llm_utils.constants import BEDROCK_EMBEDDINGS_MODEL_ID
from src.llm_utils.language_model_client import LanguageModelClient


# Fixture to initialize cache
@pytest.fixture
def cache():
    """Fixture to initialize the cache with embeddings."""
    llm_client = LanguageModelClient()
    # Initialize the embeddings model (adjust as needed for your environment)
    embeddings_model = llm_client.initialize_bedrock_embeddings_model()
    cache = Cache(embeddings_model=embeddings_model)
    return cache


def test_cache_hit(cache):
    """Test the cache hit scenario for vulnerability analysis."""
    # Sample input for testing
    criteria = "Perl"

    # Mocked response for testing cache update and lookup
    mocked_response = "Mocked Analysis Response"

    # Update the cache with the generated key, index, and mocked response
    cache.update(
        cache_key=criteria,
        llm_string=BEDROCK_EMBEDDINGS_MODEL_ID,
        value=mocked_response,
    )

    # Lookup the cached response
    cached_response = cache.lookup(
        cache_key=criteria, llm_string=BEDROCK_EMBEDDINGS_MODEL_ID
    )

    # Assert that the cached response matches the expected (mocked) response
    assert cached_response == [Generation(text=mocked_response)]
