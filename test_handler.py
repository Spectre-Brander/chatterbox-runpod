"""
Local test for the Chatterbox TTS RunPod handler.

Usage (no GPU required for the test harness itself):
    python test_handler.py

This uses RunPod's built-in local test mode: it feeds a fake job to
the handler and prints the result without connecting to RunPod's API.
"""

import json
import sys

# Simulate a RunPod local test by injecting --test_input before
# the handler calls runpod.serverless.start().

TEST_JOB = {
    "id": "test-local-001",
    "input": {
        "text": "Hello! This is a test of the Chatterbox text to speech system.",
        "output_format": "wav",
    },
}

if __name__ == "__main__":
    sys.argv = [
        "handler.py",
        "--test_input",
        json.dumps(TEST_JOB),
    ]

    # Importing handler triggers model load + runpod.serverless.start()
    # which will detect --test_input and run the handler once locally.
    import handler  # noqa: F401
