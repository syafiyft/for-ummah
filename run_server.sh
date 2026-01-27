#!/bin/bash
# Run Uvicorn server with asyncio loop to support Playwright scraper
uvicorn src.api.main:app --reload --port 8000 --loop asyncio
