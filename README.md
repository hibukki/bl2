# GPT Bandwidth Protection Demo

This project demonstrates a (very simplified) proof-of-concept for protecting Large Language Model (LLM) weights from being downloaded through API requests. The core idea is to implement a bandwidth-limiting proxy that tracks and restricts the total amount of data transferred from the model.

## How it Works

The project consists of two main components:

1. **GPT0 Server** (`/gpt0` endpoint)
   - Simulates a basic LLM API endpoint
   - Returns simple responses (in this demo, just "hello world")

2. **Limited Proxy** (`/limited-gpt0` endpoint)
   - Acts as a proxy to the GPT0 server
   - Tracks cumulative bandwidth usage
   - Returns 429 (Too Many Requests) when bandwidth limit is exceeded

## Installation

### Install poetry dependencies

```bash
poetry install
```

### Run the demo

```bash
poetry run python test_gpt.py
```

## Limitations

- TLDR: This is extremely simplified in many ways.
- This was made very quickly w Claude.
