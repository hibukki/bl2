import time
import subprocess
import sys
import signal
import os
from typing import List, Optional
import socket
from contextlib import closing
import requests

def find_free_port() -> int:
    """Find a free port to use"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

def start_gpt0_server(
    port: Optional[int] = None,
    response_delay: float = 0.01,
) -> tuple[subprocess.Popen, str]:
    """Start a GPT0 server instance
    
    Args:
        port: Port to use (if None, will find a free port)
        response_delay: Artificial delay for responses in seconds
    
    Returns:
        Tuple of (server process, server URL)
    """
    if port is None:
        port = find_free_port()
    
    server = subprocess.Popen(
        [sys.executable, "main.py", "--gpt0", "--port", str(port),
         "--response-delay", str(response_delay)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    url = f"http://localhost:{port}"
    print(f"Starting GPT0 server with {response_delay}s response delay")
    
    # Give server time to start
    time.sleep(2)
    
    return server, url

def start_limited_server(
    gpt0_url: str,
    port: Optional[int] = None,
    bandwidth_limit: int = 1000
) -> tuple[subprocess.Popen, str]:
    """Start a limited server instance
    
    Args:
        gpt0_url: URL of the GPT0 server
        port: Port to use (if None, will find a free port)
        bandwidth_limit: Bandwidth limit in bytes
    
    Returns:
        Tuple of (server process, server URL)
    """
    if port is None:
        port = find_free_port()



    command = [
        sys.executable, "main.py", "--limited", "--port", str(port),
        "--gpt0-url", gpt0_url, "--bandwidth-limit", str(bandwidth_limit)
    ]
    print(f"Starting limited server with bandwidth limit {bandwidth_limit} bytes")
    
    server = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    url = f"http://localhost:{port}"
    
    # Give server time to start
    time.sleep(2)
    
    return server, url

def cleanup_servers(servers: List[Optional[subprocess.Popen]]):
    """Cleanup server processes"""
    for server in servers:
        if server:
            if os.name == 'nt':  # Windows
                server.kill()
            else:  # Unix
                server.send_signal(signal.SIGTERM)
            server.wait()

def make_requests(url: str, n: int) -> float:
    """Make n requests to url and return total duration"""
    start = time.time()
    for i in range(n):
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Request failed with status {r.status_code}: {r.text} (after {i+1} requests)")
    return time.time() - start

def start_servers(bandwidth_limit: int = 1000) -> tuple[subprocess.Popen, subprocess.Popen, str, str]:
    """Start both GPT0 and limited servers
    
    Args:
        bandwidth_limit: Bandwidth limit for limited server in bytes
    
    Returns:
        Tuple of (gpt0_server, limited_server, gpt0_url, limited_url)
    """
    gpt0_server, gpt0_url = start_gpt0_server()
    limited_server, limited_url = start_limited_server(gpt0_url, bandwidth_limit=bandwidth_limit)
    return gpt0_server, limited_server, gpt0_url, limited_url

class ServerFixture:
    """Context manager for server setup and cleanup"""
    def __init__(self, max_bandwidth_bytes: int = 1000):
        self.max_bandwidth = max_bandwidth_bytes
        self.gpt0_server = None
        self.limited_server = None
        self.gpt0_url = None
        self.limited_url = None

    def __enter__(self):
        self.gpt0_server, self.gpt0_url = start_gpt0_server()
        self.limited_server, self.limited_url = start_limited_server(
            self.gpt0_url, 
            bandwidth_limit=self.max_bandwidth
        )
        return self.gpt0_url, self.limited_url

    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_servers([self.gpt0_server, self.limited_server])
        print("Servers cleaned up")

def limited_server(max_bandwidth_bytes: int = 1000):
    """Get a limited server with specified bandwidth limit.
    Can be used as a context manager or pytest fixture.
    
    Args:
        max_bandwidth_bytes: Maximum bandwidth in bytes
        
    Usage:
        # As context manager:
        with limited_server(1000) as (gpt0_url, limited_url):
            # run tests...
            
        # As pytest fixture:
        @pytest.fixture
        def test_server():
            return limited_server(1000)
    """
    return ServerFixture(max_bandwidth_bytes)
