import time
import requests
import subprocess
import sys
import signal
import atexit
import os
from typing import List
import socket
from contextlib import closing

def find_free_port() -> int:
    """Find a free port to use"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

def start_limited_server(gpt0_url: str, bandwidth_limit: int = 1000) -> tuple[subprocess.Popen, str]:
    """Start a limited server instance
    
    Args:
        gpt0_url: URL of the GPT0 server
        bandwidth_limit: Bandwidth limit in bytes (default: 1000)
    """
    limited_port = find_free_port()
    
    limited_server = subprocess.Popen(
        [sys.executable, "main.py", "--limited", "--port", str(limited_port),
         "--gpt0-url", gpt0_url, "--bandwidth-limit", str(bandwidth_limit)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    limited_url = f"http://localhost:{limited_port}"
    
    # Give server time to start
    time.sleep(2)
    
    return limited_server, limited_url

def start_servers() -> tuple[subprocess.Popen, subprocess.Popen, str, str]:
    """Start both GPT0 and limited servers, return the processes and their URLs"""
    # Find free port
    gpt0_port = find_free_port()
    
    # Start GPT0 server with 0.01s delay
    gpt0_server = subprocess.Popen(
        [sys.executable, "main.py", "--gpt0", "--port", str(gpt0_port), "--response-delay", "0.01"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    gpt0_url = f"http://localhost:{gpt0_port}"
    print(f"GPT0 server configured with 0.01s response delay")
    
    # Start limited server using the common function
    limited_server, limited_url = start_limited_server(gpt0_url)
    
    return gpt0_server, limited_server, gpt0_url, limited_url

def cleanup_servers(servers: List[subprocess.Popen]):
    """Cleanup server processes"""
    for server in servers:
        if server:
            if os.name == 'nt':  # Windows
                server.kill()
            else:  # Unix
                server.send_signal(signal.SIGTERM)
            server.wait()

def test_basic(gpt0_url: str, limited_url: str):
    r = requests.get(f"{gpt0_url}/gpt0")
    assert r.status_code == 200
    print("/gpt0 response:", r.text)

    r = requests.get(f"{limited_url}/limited-gpt0")
    if r.status_code == 200:
        print("/limited-gpt0 response:", r.text)
    else:
        print("/limited-gpt0 error:", r.text)

def make_requests(url: str, n: int) -> float:
    """Make n requests to url and return total duration"""
    start = time.time()
    for _ in range(n):
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Request failed with status {r.status_code}: {r.text} (after {_+1} requests)")
    return time.time() - start

def test_performance(gpt0_url: str, limited_url: str):
    """First restart the limited server with a high bandwidth limit"""
    num_requests = 100
    high_bandwidth = 1_000_000  # 1MB should be plenty for performance test
    
    # Restart limited server with high bandwidth
    limited_server, limited_url = start_limited_server(gpt0_url, high_bandwidth)
    
    gpt0_duration = make_requests(f"{gpt0_url}/gpt0", num_requests)
    limited_duration = make_requests(f"{limited_url}/limited-gpt0", num_requests)

    print(f"/gpt0 took {gpt0_duration:.4f}s for {num_requests} requests")
    print(f"/limited-gpt0 took {limited_duration:.4f}s for {num_requests} requests")
    
    # Clean up the high-bandwidth server
    cleanup_servers([limited_server])

def test_bandwidth_limit(limited_url: str):
    """Test that bandwidth limit is enforced"""
    print("\nTesting bandwidth limit...")
    responses = []
    count = 0
    
    while count < 1000:  # Safety limit to prevent infinite loop
        r = requests.get(f"{limited_url}/limited-gpt0")
        count += 1
        
        if r.status_code == 429:  # HTTP 429 is Too Many Requests
            print(f"Bandwidth limit hit after {count} requests")
            return True
        elif r.status_code != 200:
            print(f"Unexpected status code: {r.status_code}")
            return False
            
    print("Warning: Made 1000 requests without hitting bandwidth limit")
    return False

def restart_limited_server(limited_server: subprocess.Popen, gpt0_url: str) -> tuple[subprocess.Popen, str]:
    """Restart the limited server to reset bandwidth limit"""
    print("Restarting limited server...")
    cleanup_servers([limited_server])
    return start_limited_server(gpt0_url)

if __name__ == "__main__":
    print("Starting servers...")
    gpt0_server, limited_server, gpt0_url, limited_url = start_servers()
    servers = [gpt0_server, limited_server]
    
    # Register cleanup function
    atexit.register(cleanup_servers, servers)
    
    try:
        print(f"GPT0 server running at {gpt0_url}")
        print(f"Limited server running at {limited_url}")
        
        print("\nRunning basic tests...")
        test_basic(gpt0_url, limited_url)
        
        print("\nRunning performance tests...")
        test_performance(gpt0_url, limited_url)
        
        # Restart limited server before bandwidth test
        limited_server, limited_url = restart_limited_server(limited_server, gpt0_url)
        servers = [gpt0_server, limited_server]  # Update servers list with new limited server
        
        print("\nRunning bandwidth limit test...")
        if test_bandwidth_limit(limited_url):
            print("Bandwidth limit test passed!")
        else:
            print("Bandwidth limit test failed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Failed to connect to servers. Make sure they started properly.")
        for server in servers:
            stdout, stderr = server.communicate()
            print("\nServer output:")
            print(stdout.decode())
            print("\nServer errors:")
            print(stderr.decode())
        sys.exit(1)
    except Exception as e:
        print(f"Error during tests: {e}")
        raise
    finally:
        print("\nCleaning up servers...")
        cleanup_servers(servers)
        print("Servers cleaned up")
