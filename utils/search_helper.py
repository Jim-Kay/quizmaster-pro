"""
Utility script to search for programming solutions using SerpApi
"""
import logging
import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Get root directory
ROOT_DIR = Path(__file__).parent.parent

# Load environment variables
env_test = ROOT_DIR / ".env.test"
env_file = ROOT_DIR / ".env"

if env_file.exists():
    load_dotenv(env_file)
elif env_test.exists():
    load_dotenv(env_test)
else:
    raise FileNotFoundError("No .env or .env.test file found in root directory")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")

def search_solutions(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for programming solutions using SerpApi
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 5)
        
    Returns:
        List of search results, each containing title, link, and snippet
    """
    # Get API key
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        logger.error("SERPAPI_KEY not found in environment variables")
        return []
    
    # Log API key for debugging (first 10 chars only)
    logger.info(f"Using API key: {api_key[:10]}...")
    
    # Prepare request
    url = "https://serpapi.com/search"
    params = {
        "q": f"{query} site:stackoverflow.com OR site:github.com",
        "num": num_results,
        "engine": "google",  # Use Google's engine
        "hl": "en",          # Language: English
        "gl": "us",          # Geolocation: United States
        "key": api_key.strip()  # Ensure no whitespace
    }
    
    try:
        # Make request
        logger.info(f"Making request to {url} with query: {query}")
        logger.info(f"Params: {params}")
        
        response = requests.get(url, params=params)
        
        # Log response details for debugging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        response.raise_for_status()
        
        # Parse results
        data = response.json()
        organic = data.get("organic_results", [])[:num_results]
        
        # Format results
        results = []
        for item in organic:
            result = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            }
            results.append(result)
        
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making search request: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            logger.error(f"Response text: {e.response.text}")
        return []
    except KeyError as e:
        logger.error(f"Error parsing search results: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    query = "async fixture generator attribute error pytest-asyncio"
    results = search_solutions(query)
    
    print(f"\nSearch results for: {query}\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Link: {result['link']}")
        print(f"   {result['snippet']}\n")
