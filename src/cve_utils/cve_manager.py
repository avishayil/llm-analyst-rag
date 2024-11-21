import logging
import re
from io import StringIO
from typing import List

import pandas as pd
from charset_normalizer import from_path
from langchain_aws.embeddings.bedrock import BedrockEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from tqdm import tqdm  # For progress visualization

from src.llm_utils.vector_store import VectorStore

logger = logging.getLogger(__name__)


class CVEManager:
    def __init__(self, embeddings_model: BedrockEmbeddings, cve_csv_file_path: str):
        """
        Initialize the CVE Manager.

        Args:
            embeddings_model: The Bedrock embeddings model instance.
            cve_csv_file_path: Local CSV file path for the CVE database.
        """
        self.vector_store = VectorStore(embeddings=embeddings_model)
        self.csv_file_path = cve_csv_file_path
        self.clean_csv_file_path = "data/allitems_clean.csv"

    def clean_cve_data(self, years: list[int]):
        """
        Cleans CVE data from the given CSV file, optionally filtering by specified years.

        Args:
            csv_file (str): Path to the CSV file to be cleaned.
            years (list[int]): List of years to filter CVEs. If None, no filtering is applied.

        Returns:
            None: Saves the cleaned data back to the same CSV file.
        """
        # Detect encoding
        detected_encoding = from_path(self.csv_file_path).best().encoding
        logger.info(f"Detected file encoding: {detected_encoding}")

        # Read the raw file with detected encoding
        with open(self.csv_file_path, "r", encoding=detected_encoding) as file:
            lines = file.readlines()

        # Filter out irrelevant metadata lines with progress bar
        data_lines = []
        for line in tqdm(
            lines, desc="Cleaning CVE data", unit="line", dynamic_ncols=True
        ):
            if (
                line.strip()
                and not line.startswith('"CVE Version')
                and not line.startswith('"Date:')
                and not line.startswith('"Candidates')
                and not line.startswith('"before they')
                and not line.startswith('"provided for')
                and not line.startswith('"numbering scheme')
                and not line.startswith('"the Editorial Board')
            ):
                data_lines.append(line)

        # Join cleaned lines into a single string
        cleaned_data = "".join(data_lines)

        # Create a DataFrame
        df = pd.read_csv(StringIO(cleaned_data))

        # Filter by years if specified
        if years:
            year_pattern = re.compile(r"CVE-(\d{4})-")

            def extract_year(name):
                if isinstance(name, str):
                    match = year_pattern.search(name)
                    return int(match.group(1)) if match else None
                return None

            tqdm.pandas(desc="Filtering by year")
            df = df[df["Name"].progress_apply(extract_year).isin(years)]

        # Save the cleaned DataFrame back to the file
        df.to_csv(self.clean_csv_file_path, index=False)

    def parse_cve_data(self) -> List[Document]:
        """
        Parse the CVE CSV data into a list of Documents.

        Args:
            csv_file: Path to the CSV file.

        Returns:
            A list of parsed Documents.
        """
        loader = CSVLoader(
            file_path=self.clean_csv_file_path,
            content_columns=["Name", "Description"],
            autodetect_encoding=True,
        )
        docs: List[Document] = loader.load()
        return docs

    def index_cve_data(self):
        """
        Index CVE data into the vector store.
        """
        cve_documents = self.parse_cve_data()

        for doc in tqdm(
            cve_documents, desc="Indexing CVE data", unit="document", dynamic_ncols=True
        ):
            self.vector_store.save(documents=[doc])  # Save one document at a time

    def get_cve_data_retriever(self):
        """
        Load the vector store retriever.
        """
        return self.vector_store.load()
