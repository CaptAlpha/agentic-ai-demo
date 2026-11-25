from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

def get_google_search_results(query: str) -> dict:
    """Fetch top 5 Google search results for a query."""
    try:
        search_tool = google_search.GoogleSearchTool()
        results = search_tool.search(query, num_results=5)
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": f"Failed to fetch search results for '{query}': {e}"}

root_agent = Agent(
    name="research_agent",
    model="gemini-3.5-flash",
    description="A web research assistant",
    instruction="Answer the user's question by conducting web research and providing relevant information, use get_google_search_results to fetch information from the web.",
    tools=[get_google_search_results]
)