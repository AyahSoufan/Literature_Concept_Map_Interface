from typing import Dict, Union

import wikipedia
from requests import ConnectionError
from utils.article import WikipediaArticle


def search_wikipedia(query: str) -> Union[Dict[str, str], None]:
    """If there exist a wikipedia page with the title equal to the query it returns
    dictionary with the content of wikipedia page."""
    wikipedia.set_lang("en")
    result = None

    try:
        page_object = wikipedia.page(query, auto_suggest=False)
        result = WikipediaArticle(
            id=page_object.pageid,
            title=page_object.title,
            url=page_object.url,
            snippet=f"{page_object.content[:1000]}...",
            content=page_object.content,
        )
    except wikipedia.PageError:
        result = None
    except KeyError:
        result = None
    except ConnectionError:
        result = None
    except wikipedia.DisambiguationError as e:
        for option in e.options:
            result = search_wikipedia(option)
            if result:
                return result

    return result
