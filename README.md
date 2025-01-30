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
   - Returns an error when bandwidth limit is exceeded

## Installation

### Install poetry (and everything it depends on)

See the [official docs](https://python-poetry.org/docs/#installation)

### Python

If you're missing a python version, I recommend installing it with [pyenv](https://github.com/pyenv/pyenv).

### Install poetry dependencies

```bash
poetry install
```

### Run the demo

```bash
poetry run python test_gpt.py
```

#### Example output (this might not be up to date)

```text
Starting servers...
GPT0 server configured with 0.01s response delay
GPT0 server running at http://localhost:60922
Limited server running at http://localhost:60923

Running basic tests...
/gpt0 response: "hello world"
/limited-gpt0 response: "hello world"

Running performance tests...
/gpt0 took 1.6186s for 100 requests
/limited-gpt0 took 1.8218s for 100 requests
Restarting limited server...

Running bandwidth limit test...

Testing bandwidth limit...
Bandwidth limit hit after 77 requests
Bandwidth limit test passed!

Cleaning up servers...
Servers cleaned up
```

## Limitations

- TLDR: This is extremely simplified in many ways.
- This was made very quickly w Claude.
