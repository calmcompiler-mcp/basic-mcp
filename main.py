import os
import json
import wikipedia
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
from dotenv import load_dotenv

from starlette.responses import JSONResponse
from starlette.routing import Route

from utils.auth import create_auth0_verifier


# Load environment variables from .env file
load_dotenv()

# Get Auth0 configuration from environment
auth0_domain = os.getenv("AUTH0_DOMAIN")
resource_server_url = os.getenv("RESOURCE_SERVER_URL")

if not auth0_domain:
    raise ValueError("AUTH0_DOMAIN environment variable is required")
if not resource_server_url:
    raise ValueError("RESOURCE_SERVER_URL environment variable is required")

# Load server instructions
with open("prompts/server_instructions.md", "r") as file:
    server_instructions = file.read()

# Initialize Auth0 token verifier
token_verifier = create_auth0_verifier()

# Create an MCP server with OAuth authentication
mcp = FastMCP(
    "wiki-mcp",
    instructions=server_instructions,
    host="0.0.0.0",
    # OAuth Configuration
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{auth0_domain}/"),
        resource_server_url=AnyHttpUrl(resource_server_url),
        required_scopes=["openid", "profile", "email", "address", "phone"],
    ),
)


# Publish OAuth metadata at a well-known URL
async def oauth_metadata(request):
    return JSONResponse(
        {
            "issuer": f"https://{auth0_domain}/",
            "authorization_endpoint": f"https://{auth0_domain}/authorize",
            "token_endpoint": f"https://{auth0_domain}/oauth/token",
            "scopes_supported": [
                "openid", "profile", "email", "address", "phone", "insurance.quote"
            ],
        }
    )

# Register the route
mcp.app.routes.append(Route(
    "/.well-known/oauth-protected-resource",
    oauth_metadata
))


@mcp.tool(
    securitySchemes=[{"type": "oauth2", "scopes": ["insurance.quote"]}]
)
def personalized_insurance_quote(zip_code: str, coverage_level: str) -> str:
    """
    Fetch a personalized insurance quote for a given zip code and coverage level.
    Requires OAuth2 authentication.
    """
    # Check for token in headers
    headers = mcp.current_request_headers.get()
    token = headers.get("Authorization") if headers else None

    if not token or not token.startswith("Bearer "):
        # Return an error with WWW-Authenticate metadata to trigger login UI
        return {
            "content": [{
                "type": "text",
                "text": "Authentication required: no access token provided."
            }],
            "isError": True,
            "_meta": {
                "mcp/www_authenticate": [
                    f'Bearer resource_metadata="https://{auth0_domain}/.well-known/oauth-protected-resource", '
                    'error="invalid_token", '
                    'error_description="You need to login to continue"'
                ]
            }
        }

    # If token is present, validate and proceed
    # (replace with real backend call)
    return (
        f"Personalized insurance quote for {zip_code} with {coverage_level} coverage: "
        f"$123/month (example data)."
    )


@mcp.tool()
def fetch_wikipedia_summary(topic: str) -> str:
    """
    Fetch a summary and related links for a given topic from Wikipedia.

    Args:
        topic (str): The topic to search on Wikipedia

    Returns:
        str: Formatted summary and links
    """
    try:
        # Get summary
        summary = wikipedia.summary(topic, sentences=5, auto_suggest=True, redirect=True)

        # Get page details
        page = wikipedia.page(topic, auto_suggest=True, redirect=True)

        # Format output
        result = f"Summary for '{topic}':\n\n{summary}\n\nLinks:\n"
        for link in page.links[:10]:  # limit to first 10 links
            result += f"- {link}\n"

        return result

    except wikipedia.exceptions.DisambiguationError as e:
        return f"Topic '{topic}' is ambiguous. Possible options:\n" + "\n".join(e.options[:10])
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for topic '{topic}'."
    except Exception as e:
        raise Exception(f"Error fetching Wikipedia data: {str(e)}")


@mcp.tool()
def fetch_instructions(prompt_name: str) -> str:
    """
    Fetch instructions for a given prompt name from the prompts/ directory

    Args:
        prompt_name (str): Name of the prompt to fetch instructions for
        Available prompts: 
            - fetch_wikipedia_summary

    Returns:
        str: Instructions for the given prompt
    """
    script_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(script_dir, "prompts", f"{prompt_name}.md")
    with open(prompt_path, "r") as f:
        return f.read()


if __name__ == "__main__":
    mcp.run(transport='streamable-http')
