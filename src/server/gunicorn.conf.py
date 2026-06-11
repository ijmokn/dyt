# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.

"""Gunicorn configuration for Azure AI Agent application."""

import multiprocessing
import os

from startup import run_initialization


def on_starting(server):
    """
    Hook called once before workers start.
    
    Initializes Azure AI resources (agent, search tools, evaluation).
    """
    run_initialization()


# ============================================================================
# Gunicorn Server Configuration
# ============================================================================

# Server socket
bind = "0.0.0.0:50505"

# Worker processes
num_cpus = multiprocessing.cpu_count()
workers = (num_cpus * 2) + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 50
timeout = 120

# Application preloading
# Load application before forking workers (required for on_starting hook)
# See: https://docs.gunicorn.org/en/stable/settings.html
preload_app = True

# Logging
log_file = "-"  # Log to stdout

# Development mode
if not os.getenv("RUNNING_IN_PRODUCTION"):
    reload = True


# ============================================================================
# Direct Execution (for testing)
# ============================================================================

if __name__ == "__main__":
    import asyncio
    import logging
    from startup import initialize_resources
    
    logger = logging.getLogger("azureaiapp")
    logger.info("Running resource initialization directly...")
    asyncio.run(initialize_resources())
    logger.info("Initialization complete")