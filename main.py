from fastapi import FastAPI
import uvicorn
import argparse
from routers import gpt0, gpt0limited

def create_app(enable_gpt0: bool = True, 
               enable_limited: bool = True, 
               gpt0_url: str = "http://localhost:8000", 
               bandwidth_limit_bytes: int = 1000, 
               response_delay_seconds: float = 0,
               ):
    # Create a new FastAPI instance
    app = FastAPI()
    
    if enable_gpt0:
        app.include_router(gpt0.configure_router(response_delay_seconds=response_delay_seconds))
    
    if enable_limited:
        app.include_router(gpt0limited.configure_router(
            bandwidth_limit_bytes=bandwidth_limit_bytes,
            base_url=gpt0_url
        ))
    
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
