import argparse
import logging
import os
import subprocess
import sys
import time

import requests

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def wait_for_moto_service():
    retries = 5
    for i in range(retries):
        try:
            response = requests.get("http://localhost:3000")
            if response.status_code == 200:
                logger.info("Moto service is up!")
                return True
        except requests.ConnectionError:
            logger.info(f"Moto service not available, retrying ({i + 1}/{retries})...")
            time.sleep(3)  # Adjust sleep duration if necessary
    raise RuntimeError("Failed to connect to Moto service after retries")


def start_docker_compose():
    logger.info("Starting Docker Compose services...")
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(result.stdout)  # Log stdout for debugging
        logger.info(result.stderr)  # Log stderr for debugging
        wait_for_moto_service()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting Docker Compose: {e.stderr}")
        raise


def stop_docker_compose():
    logger.info("Stopping Docker Compose services...")
    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(result.stdout)  # Log stdout for debugging
        logger.info(result.stderr)  # Log stderr for debugging
    except subprocess.CalledProcessError as e:
        logger.error(f"Error stopping Docker Compose: {e.stderr}")
        raise


def initialize_backend():
    """Run the init_backend.py script and extract the necessary values from the logs."""
    result = subprocess.run(
        ["python", "scripts/init_backend.py", "--is-moto"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"Error initializing backend: {result.stderr}")
        raise RuntimeError("init_backend.py script failed")

    logger.info(result.stdout)  # Log stdout for debugging


def main(action):
    """Main function to start or stop Docker services based on the action."""
    if action == "up":
        start_docker_compose()  # Start Docker Compose and wait for services
        initialize_backend()  # Initialize the backend
    elif action == "down":
        stop_docker_compose()  # Stop Docker Compose services
    else:
        logger.error(
            "Invalid action. Use 'up' to spin up or 'down' to spin down the environment."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control Docker Compose environment.")
    parser.add_argument(
        "--action",
        choices=["up", "down"],
        help="Choose whether to spin up ('up') or spin down ('down') the testing environment.",
    )

    args = parser.parse_args()
    main(args.action)
