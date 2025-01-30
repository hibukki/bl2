from fastapi import FastAPI, HTTPException, Response
import uvicorn
import argparse
import requests
import time

app = FastAPI()
ALLOWED_BANDWIDTH_BYTES = 1000  # Default bandwidth limit in bytes
gpt0_url = None
gpt0_response_delay = 0

@app.get("/gpt0")
def gpt0():
    if gpt0_response_delay > 0:
        time.sleep(gpt0_response_delay)
    return "hello world"

@app.get("/limited-gpt0")
def limited_gpt0():
    global ALLOWED_BANDWIDTH_BYTES
    
    # Get response from gpt0 endpoint
    response = requests.get(f"{gpt0_url}/gpt0")
    response.raise_for_status()
    stub_response = response.text

    response_size_bytes = len(stub_response.encode('utf-8'))
    if ALLOWED_BANDWIDTH_BYTES - response_size_bytes < 0:
        raise HTTPException(status_code=429, detail="Bandwidth limit exceeded")

    ALLOWED_BANDWIDTH_BYTES -= response_size_bytes
    return Response(content=stub_response)

def create_app(enable_gpt0: bool = True, enable_limited: bool = True, gpt0_url: str = "http://localhost:8000", 
               bandwidth_limit_bytes: int = 1000, response_delay_seconds: float = 0):
    # Create a new FastAPI instance
    app = FastAPI()
    
    if enable_gpt0:
        global gpt0_response_delay
        gpt0_response_delay = response_delay_seconds
        
        @app.get("/gpt0")
        def gpt0():
            if gpt0_response_delay > 0:
                time.sleep(gpt0_response_delay)
            return "hello world"
    
    if enable_limited:
        global ALLOWED_BANDWIDTH_BYTES
        ALLOWED_BANDWIDTH_BYTES = bandwidth_limit_bytes
        
        @app.get("/limited-gpt0")
        def limited_gpt0():
            global ALLOWED_BANDWIDTH_BYTES
            
            # Get the actual data from gpt0 endpoint
            try:
                response = requests.get(f"{gpt0_url}/gpt0")
                response.raise_for_status()
                stub_response = response.text
            except requests.RequestException as e:
                raise HTTPException(status_code=503, detail=f"Failed to fetch from GPT0: {str(e)}")

            response_size_bytes = len(stub_response.encode('utf-8'))
            if ALLOWED_BANDWIDTH_BYTES - response_size_bytes < 0:
                raise HTTPException(status_code=429, detail="Bandwidth limit exceeded")

            ALLOWED_BANDWIDTH_BYTES -= response_size_bytes
            return Response(content=stub_response)
    
    return app

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run FastAPI server with selected endpoints')
    parser.add_argument('--gpt0', action='store_true', help='Enable /gpt0 endpoint')
    parser.add_argument('--limited', action='store_true', help='Enable /limited-gpt0 endpoint')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Host to run the server on')
    parser.add_argument('--gpt0-url', type=str, default="http://localhost:8000",
                      help='URL of the GPT0 service (e.g., http://localhost:8000)')
    parser.add_argument('--bandwidth-limit', type=int, default=1000,
                      help='Bandwidth limit in bytes for the limited endpoint')
    parser.add_argument('--response-delay', type=float, default=0,
                      help='Artificial delay in seconds for GPT0 response')
    
    args = parser.parse_args()
    
    # If no endpoints are specified, enable both by default
    if not (args.gpt0 or args.limited):
        args.gpt0 = True
        args.limited = True
    
    # Create the app with specified endpoints
    app = create_app(
        enable_gpt0=args.gpt0,
        enable_limited=args.limited,
        gpt0_url=args.gpt0_url,
        bandwidth_limit_bytes=args.bandwidth_limit,
        response_delay_seconds=args.response_delay
    )
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)
