from tavily import TavilyClient

from app.config.settings import TAVILY_API_KEY


tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)


def web_search(
    query: str
) -> dict:
    """
    Search the web for current and relevant information.

    Args:
        query: The search query.

    Returns:
        Search results containing titles, URLs and content.
    """

    response = tavily_client.search(
        query=query,
        max_results=5
    )

    results = []

    for result in response.get(
        "results",
        []
    ):

        results.append(
            {
                "title": result.get(
                    "title",
                    ""
                ),
                "url": result.get(
                    "url",
                    ""
                ),
                "content": result.get(
                    "content",
                    ""
                ),
                "score": result.get(
                    "score",
                    0
                )
            }
        )

    return {
        "query": query,
        "results": results
    }