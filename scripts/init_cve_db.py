import logging
import os
import sys
from typing import List

from src.cve_utils.cve_manager import CVEManager
from src.llm_utils.language_model_client import LanguageModelClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def initialize_language_model() -> LanguageModelClient:
    """
    Initialize and return the language model client.

    Returns:
        LanguageModelClient: Initialized language model client.
    """
    try:
        logging.info("Initializing Language Model Client...")
        return LanguageModelClient()
    except Exception as e:
        logging.error(f"Failed to initialize Language Model Client: {e}")
        raise


def initialize_cve_manager(embeddings_model, cve_csv_file_path: str) -> CVEManager:
    """
    Initialize and return the CVEManager instance.

    Args:
        embeddings_model: Embeddings model to use.
        csv_file_path (str): Path to the CSV file with CVE data.

    Returns:
        CVEManager: Initialized CVE manager.
    """
    try:
        logging.info("Initializing CVEManager...")
        return CVEManager(
            embeddings_model=embeddings_model,
            cve_csv_file_path=cve_csv_file_path,
        )
    except Exception as e:
        logging.error(f"Failed to initialize CVEManager: {e}")
        raise


def main(cve_csv_file_path: str, years: List[int]) -> None:
    """
    Main execution function.

    Args:
        csv_file_path (str): Path to the CSV file containing CVE data.
        years (List[int]): List of years to filter CVE data.
    """
    try:
        logging.info("Starting the process...")

        # Initialize Language Model and Embeddings
        llm_client = initialize_language_model()
        embeddings_model = llm_client.initialize_bedrock_embeddings_model()

        # Initialize CVEManager
        cve_manager = initialize_cve_manager(embeddings_model, cve_csv_file_path)

        # Clean and Index CVE data
        logging.info("Cleaning CVE data...")
        cve_manager.clean_cve_data(years=years)

        logging.info("Indexing CVE data...")
        cve_manager.index_cve_data()

        logging.info("Process completed successfully.")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
    except ValueError as e:
        logging.error(f"Invalid data encountered: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    try:
        # Specify the CSV file path and years to process
        CVE_CSV_FILE_PATH = "data/allitems.csv"
        YEARS = [2023, 2024]

        # Validate input
        if not os.path.exists(CVE_CSV_FILE_PATH):
            logging.error(f"CSV file '{CVE_CSV_FILE_PATH}' does not exist.")
            sys.exit(1)

        main(cve_csv_file_path=CVE_CSV_FILE_PATH, years=YEARS)
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user.")
        sys.exit(1)
