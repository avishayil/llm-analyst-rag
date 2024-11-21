import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BedrockModelConfig(BaseModel):
    bedrock_model_id: str
    temperature: float = Field(default=0.5, ge=0, le=1)
    top_p: float = Field(default=1, ge=0, le=1)
    top_k: int = Field(default=250, gt=0)
    max_tokens: int = Field(default=4096, ge=0, le=4096)

    def get_model_id(self) -> str:
        """Returns the model ID."""
        return self.bedrock_model_id

    def get_model_kwargs(self) -> dict:
        """Returns model kwargs as a dictionary."""
        # Assuming the correct method is dict() instead of model_dump()
        return self.model_dump(exclude={"bedrock_model_id"})

    def update_config(self, **kwargs) -> None:
        """
        Updates the model configuration with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if key not in ["bedrock_model_id"]:
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    logger.warning(f"Invalid configuration key: {key}")


class BedrockEmbeddingsModelConfig(BaseModel):
    bedrock_embeddings_model_id: str

    def get_model_id(self) -> str:
        """Returns the embeddings model ID."""
        return self.bedrock_embeddings_model_id

    def get_model_kwargs(self) -> dict:
        """Returns model kwargs as a dictionary."""
        # Assuming the correct method is dict() instead of model_dump()
        return self.model_dump(exclude={"bedrock_embeddings_model_id"})

    def update_config(self, **kwargs) -> None:
        """
        Updates the model configuration with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if key not in ["bedrock_embeddings_model_id"]:
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    logger.warning(f"Invalid configuration key: {key}")
