# app.py
import logging

import gradio as gr
import uvicorn
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from src.auth_utils.config import LOG_LEVEL, SECRET_KEY
from src.llm_apps.load_apps import load_apps  # Import the load_apps function
from src.routes import api_router, main_router

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def init_app() -> FastAPI:
    """
    Initialise a FastApi app, with all the required routes and the
    :return: FastAPI initialized app
    """

    # FastAPI instance
    limiter = Limiter(key_func=get_remote_address)

    fast_api_app = FastAPI()
    fast_api_app.state.limiter = limiter
    fast_api_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add Session Middleware
    fast_api_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

    # Register Routes
    # Register the API router with the `/api/v1` prefix
    fast_api_app.include_router(api_router)

    # Register the main router for non-API routes
    fast_api_app.include_router(main_router)

    with gr.Blocks(
        css="""
        #centered-logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 200px;
            height: auto;
        }

        .button-container {
            text-align: center;
            margin-top: 20px;
        }

        #info-text {
            text-align: center;
            margin-top: 10px;
        }
    """
    ) as login_interface:
        gr.Image(
            "./src/static/images/logo.png",
            elem_id="centered-logo",  # Centering the logo
            show_label=False,
            show_download_button=False,
        )
        gr.Markdown(
            """
            ## Welcome to the Vulnerability Analyst
            Please log in to access advanced features and generate tailored analysis.
            """,
            elem_id="info-text",
        )
        gr.Markdown(
            """
            ### Features:
            - Generate analysis and trends based on CVE details.
            - Seamlessly integrated with AWS Cognito for secure access.
            - Powered by cutting-edge AI technology for vulnerability management.
            """,
            elem_id="info-text",
        )
        with gr.Row():
            gr.Markdown(
                """
                **Note:** Use your registered credentials to log in. If you need help,
                visit our [support page](#) or contact the administrator.
                """,
                elem_id="info-text",
            )
        with gr.Row(elem_classes=["button-container"]):
            gr.Button("Login", link="/login")

    gr.mount_gradio_app(fast_api_app, login_interface, path="/login-page")

    # Load all apps and setup their Gradio interfaces
    load_apps(fast_api_app)

    return fast_api_app


def main():
    try:
        fast_api_app = init_app()

        # Start the server
        uvicorn.run(fast_api_app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
