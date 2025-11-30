"""
ngrok Tunnel Server Runner - GPT Actions Connector

Polymath MCP HTTP Server tunneling via ngrok
for GPT Actions access.
"""

import os
import sys
import io
import time
import threading
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_uvicorn(port: int):
    """Run uvicorn server"""
    import uvicorn
    from src.http_server import app

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def print_openapi_spec(base_url: str):
    """Print OpenAPI spec for GPT Actions"""
    spec = f"""
================================================================================
GPT Actions OpenAPI Spec
================================================================================

Paste the following into GPT Builder:

{{
  "openapi": "3.1.0",
  "info": {{
    "title": "Polymath MCP API",
    "description": "Polymath API for interdisciplinary knowledge fusion",
    "version": "2.0.0"
  }},
  "servers": [
    {{
      "url": "{base_url}"
    }}
  ],
  "paths": {{
    "/api/search": {{
      "get": {{
        "summary": "Search concepts",
        "operationId": "searchConcepts",
        "parameters": [
          {{"name": "q", "in": "query", "required": true, "schema": {{"type": "string"}}}},
          {{"name": "limit", "in": "query", "schema": {{"type": "integer", "default": 10}}}}
        ],
        "responses": {{
          "200": {{"description": "Search results"}}
        }}
      }}
    }},
    "/api/fusion/suggest": {{
      "post": {{
        "summary": "Analyze fusion possibilities",
        "operationId": "suggestFusion",
        "requestBody": {{
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "object",
                "properties": {{
                  "concept_a": {{"type": "string"}},
                  "concept_b": {{"type": "string"}}
                }},
                "required": ["concept_a", "concept_b"]
              }}
            }}
          }}
        }},
        "responses": {{
          "200": {{"description": "Fusion analysis result"}}
        }}
      }}
    }},
    "/api/socratic/start": {{
      "post": {{
        "summary": "Start Socratic dialogue",
        "operationId": "startSocratic",
        "requestBody": {{
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "object",
                "properties": {{
                  "topic": {{"type": "string"}},
                  "focus": {{"type": "string", "default": "explore"}}
                }},
                "required": ["topic"]
              }}
            }}
          }}
        }},
        "responses": {{
          "200": {{"description": "Session start result"}}
        }}
      }}
    }},
    "/api/socratic/continue": {{
      "post": {{
        "summary": "Continue Socratic dialogue",
        "operationId": "continueSocratic",
        "requestBody": {{
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "object",
                "properties": {{
                  "session_id": {{"type": "string"}},
                  "response": {{"type": "string"}}
                }},
                "required": ["session_id", "response"]
              }}
            }}
          }}
        }},
        "responses": {{
          "200": {{"description": "Next question"}}
        }}
      }}
    }},
    "/api/learning/path": {{
      "post": {{
        "summary": "Generate learning path",
        "operationId": "getLearningPath",
        "requestBody": {{
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "object",
                "properties": {{
                  "start_concept": {{"type": "string"}},
                  "path_type": {{"type": "string", "default": "spiral"}}
                }},
                "required": ["start_concept"]
              }}
            }}
          }}
        }},
        "responses": {{
          "200": {{"description": "Learning path"}}
        }}
      }}
    }},
    "/api/domains": {{
      "get": {{
        "summary": "List academic domains",
        "operationId": "getDomains",
        "responses": {{
          "200": {{"description": "30 domains list"}}
        }}
      }}
    }},
    "/api/fusion/patterns": {{
      "get": {{
        "summary": "Get 7 fusion patterns",
        "operationId": "getFusionPatterns",
        "responses": {{
          "200": {{"description": "Fusion patterns list"}}
        }}
      }}
    }}
  }}
}}

================================================================================
"""
    print(spec)


def main():
    """Main execution"""
    from pyngrok import ngrok, conf

    PORT = 8765  # Fixed port

    # ngrok authtoken
    NGROK_AUTHTOKEN = "362PncOvN4vjqtWIsSrBqRMGBg3_3npAUm6RuQYTGUamXmR87"

    print("""
================================================================================
         Polymath MCP - GPT Actions Connector
================================================================================
    """)

    # Configure ngrok
    conf.get_default().auth_token = NGROK_AUTHTOKEN

    print("[OK] ngrok configured")

    # Start uvicorn server (separate thread)
    print(f"[*] Starting HTTP server (port {PORT})...")
    server_thread = threading.Thread(
        target=run_uvicorn,
        args=(PORT,),
        daemon=True
    )
    server_thread.start()

    # Wait for server to be ready
    time.sleep(3)

    # Start ngrok tunnel
    print("[*] Starting ngrok tunnel...")

    try:
        public_url = ngrok.connect(PORT, "http")
        ngrok_url = str(public_url.public_url)

        print(f"""
================================================================================
  [OK] Server is ready!
================================================================================

  Public URL: {ngrok_url}

  API Docs: {ngrok_url}/docs
  OpenAPI:  {ngrok_url}/openapi.json

================================================================================
        """)

        # Print OpenAPI spec
        print_openapi_spec(ngrok_url)

        print("\n[*] Press Ctrl+C to stop.\n")

        try:
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Shutting down server...")
            ngrok.disconnect(public_url.public_url)
            ngrok.kill()

    except Exception as e:
        print(f"[ERROR] Failed to start ngrok: {e}")
        print("        Make sure your authtoken is valid.")


if __name__ == "__main__":
    main()
