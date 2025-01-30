import requests
from test_utils import (
    limited_server,
    make_requests,
)

def test_basic():
    with limited_server() as (gpt0_url, limited_url):
        r = requests.get(f"{gpt0_url}/gpt0")
        assert r.status_code == 200
        print("/gpt0 response:", r.text)

        r = requests.get(f"{limited_url}/limited-gpt0")
        if r.status_code == 200:
            print("/limited-gpt0 response:", r.text)
        else:
            print("/limited-gpt0 error:", r.text)

def test_performance():
    with limited_server(max_bandwidth_bytes=1_000_000) as (gpt0_url, limited_url):
        num_requests = 100
        
        gpt0_duration = make_requests(f"{gpt0_url}/gpt0", num_requests)
        limited_duration = make_requests(f"{limited_url}/limited-gpt0", num_requests)

        print(f"/gpt0 took {gpt0_duration:.4f}s for {num_requests} requests")
        print(f"/limited-gpt0 took {limited_duration:.4f}s for {num_requests} requests")

def test_bandwidth_limit():
    """Test that bandwidth limit is enforced"""
    with limited_server(max_bandwidth_bytes=1000) as (_, limited_url):
        print("\nTesting bandwidth limit...")
        count = 0
        MAX_REQUESTS = 1000
        while count < MAX_REQUESTS:  # Safety limit to prevent infinite loop
            r = requests.get(f"{limited_url}/limited-gpt0")
            count += 1
            
            if r.status_code == 429:  # HTTP 429 is Too Many Requests
                print(f"Bandwidth limit hit after {count} requests")
                return True
            elif r.status_code != 200:
                print(f"Unexpected status code: {r.status_code}")
                return False
                
        assert False, f"Made {MAX_REQUESTS} requests without hitting bandwidth limit"

if __name__ == "__main__":
    print("Running basic tests...")
    test_basic()
    
    print("\nRunning performance tests...")
    test_performance()
    
    print("\nRunning bandwidth limit test...")
    if test_bandwidth_limit():
        print("Bandwidth limit test passed!")
    else:
        print("Bandwidth limit test failed!")
