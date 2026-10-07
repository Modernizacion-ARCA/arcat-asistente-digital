from .base import *


DEBUG = False

# CI uses ephemeral credentials supplied by the workflow. OpenRouter remains disabled:
# tests must mock every external LLM request and never depend on a real API key.
