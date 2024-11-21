# load_apps.py
from fastapi import FastAPI

from src.llm_apps.vulnerability_trend_analyst import VulnerabilityTrendAnalyst


def load_apps(fastapi_app: FastAPI):
    return [
        VulnerabilityTrendAnalyst(app=fastapi_app),
    ]
