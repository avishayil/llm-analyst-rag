import logging
import os
from typing import Dict, Optional

import boto3
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts.prompt import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_aws.embeddings.bedrock import BedrockEmbeddings
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback
from langchain_community.vectorstores.redis import RedisVectorStoreRetriever
from langchain_core.output_parsers import XMLOutputParser

from src.llm_utils.constants import BEDROCK_EMBEDDINGS_MODEL_ID, BEDROCK_MODEL_ID
from src.models.llm_models import BedrockEmbeddingsModelConfig, BedrockModelConfig

logger = logging.getLogger(__name__)


class LanguageModelClient:
    def __init__(self) -> None:
        """
        Initializes the language model client with the specified model ID and keyword arguments.
        """
        self.bedrock_model_config: Optional[BedrockModelConfig] = None
        self.bedrock_embeddings_model_config: Optional[BedrockEmbeddingsModelConfig] = (
            None
        )

    def initialize_bedrock_model(self) -> ChatBedrock:
        """
        Initializes the language model based on the provided model ID and configuration.

        :return: An instance of the Bedrock model or None if initialization fails.
        """
        try:
            self.bedrock_model_config = BedrockModelConfig(
                bedrock_model_id=BEDROCK_MODEL_ID
            )
            llm = ChatBedrock(
                model=self.bedrock_model_config.get_model_id(),
                model_kwargs=self.bedrock_model_config.get_model_kwargs(),
                client=self.initialize_boto3_bedrock_client(),
            )
            return llm
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    def initialize_bedrock_embeddings_model(self) -> BedrockEmbeddings:
        """
        Initializes the language model based on the provided model ID and configuration.

        :return: An instance of the Bedrock model or None if initialization fails.
        """
        try:
            self.bedrock_embeddings_model_config = BedrockEmbeddingsModelConfig(
                bedrock_embeddings_model_id=BEDROCK_EMBEDDINGS_MODEL_ID
            )
            embeddings_model = BedrockEmbeddings(
                model_id=self.bedrock_embeddings_model_config.get_model_id(),
                model_kwargs=self.bedrock_embeddings_model_config.get_model_kwargs(),
                client=self.initialize_boto3_bedrock_client(),
            )
            return embeddings_model
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            return None

    @staticmethod
    def initialize_boto3_bedrock_client() -> Optional[boto3.client]:
        """
        Initializes the Boto3 client for the Bedrock API.

        :return: An instance of the Boto3 client for the Bedrock API or None if initialization fails.
        """
        try:
            return boto3.client(
                "bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
        except Exception as e:
            logger.error(f"Error initializing Boto3 client: {e}")
            return None

    def invoke_chain(
        self,
        llm: ChatBedrock,
        retriever: RedisVectorStoreRetriever,
        prompt: PromptTemplate,
        parser: XMLOutputParser,
    ) -> Optional[Dict[str, int]]:
        """
        Uses the initialized language model to predict the output based on the given prompt.

        :param llm: An instance of the language model to use for generating the response.
        :param prompt: The prompt to send to the language model.
        :return: The predicted output from the language model as a dictionary or None if an error occurs.
        """
        try:

            with get_bedrock_anthropic_callback() as cb:
                question_answer_chain = create_stuff_documents_chain(
                    llm=llm, prompt=prompt, output_parser=parser
                )
                rag_chain = create_retrieval_chain(
                    retriever=retriever, combine_docs_chain=question_answer_chain
                )
                model_response = rag_chain.invoke(
                    {
                        "input": "Provide execution to the prompt and retrieve the response."
                    }
                )
                logger.info(f"Model Response: {model_response}")

                used_tokens = cb.total_tokens
                logger.info(f"Used tokens: {used_tokens}")

                result = {
                    "used_tokens": used_tokens,
                    "model_response": model_response["answer"]["output"],
                }
                return result
        except Exception as e:
            logger.error(f"Error invoking chain: {e}")
            raise Exception(f"Error invoking chain: {e}")
