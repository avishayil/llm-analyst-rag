from src.llm_utils.language_model_client import LanguageModelClient


def test_initialize_bedrock_model():
    """Test that the Bedrock model initializes correctly."""
    client = LanguageModelClient()
    model = client.initialize_bedrock_model()
    assert model is not None


def test_invoke_chain(monkeypatch):
    """Test the invoke_chain method with a mocked response."""
    client = LanguageModelClient()

    def mock_invoke_chain(llm, retriever, prompt, parser):
        return {
            "answer": {
                "output": [
                    {
                        "trend": [
                            {
                                "summary": "Trend shows massive growth in critical vulnerabilities over the last 5 years."
                            }
                        ]
                    }
                ]
            },
            "used_tokens": 917,
        }

    monkeypatch.setattr(client, "invoke_chain", mock_invoke_chain)

    result = client.invoke_chain(None, None, None, None)
    assert (
        "Trend shows massive growth in critical vulnerabilities over the last 5 years."
        in result["answer"]["output"][0]["trend"][0]["summary"]
    )
