import requests
import json
import re
from typing import List

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils.article import Article


def highlighter(doc: str, es_highlighted_texts: List[str]):
    # pattern = re.compile(r"<em>(.*?)</em>")
    # highlight_terms = []
    # for line in es_highlighted_texts:
    #     highlight_terms += re.findall(pattern, line)

    highlighted_abstract = ""
    highlighted_snippet = ""
    for term in doc.split():
        #if re.sub(r"[^\w]", "", term) in highlight_terms:
            #term = "<em>" + term + "</em>"
        term += " "
        highlighted_abstract += term
        if len(highlighted_snippet) < 200:
            highlighted_snippet += term
    highlighted_snippet = highlighted_snippet + "...."
    return highlighted_abstract[:-1], highlighted_snippet[:-1]


def search(query: str, index: str, top_k: int):
    headers = {"Content-type": "application/json"}
    res = requests.post(
        "http://localhost:9880" + "/search",
        data=json.dumps({"query": query, "es_index": index, "es_top_k": top_k}),
        headers=headers,
    )
    results = res.json()["results"]
    candidate_list = []
    all_CSO_keywords = set()
    for candidate in results["hits"]["hits"]:
        #all_CSO_keywords.update(candidate["_source"].get("CSO_keywords")['union'])
        #print(all_CSO_keywords)

        doc_text = candidate["_source"].get("abstract")
        if doc_text and "abstract" in candidate["highlight"]:
            abstract, snippet = highlighter(doc_text, candidate["highlight"]["abstract"])
        else:
            abstract = candidate["_source"].get("abstract")
            snippet = candidate["_source"].get("abstract")[:300]

        authors_raw = candidate["_source"].get("authors")
        if authors_raw:
            author_details = [
                author["name"] for author in authors_raw if "name" in author
            ]
        else:
            author_details = []

        # venue_raw = candidate["_source"].get("venue")
        # if venue_raw:
        #     venue = venue_raw.get("name_d")
        # else:
        #     venue = ""
        #
        # pdf = candidate["_source"].get("pdf")

        url_candidates = candidate["_source"].get("url")
        url = ""
        if url_candidates:
            url = url_candidates[0]

        # keywords_snippet = {}
        # keywords_rest = {}
        # index_i = 0
        # for k, v in sorted(candidate["_source"].get("keywords").items(), key=lambda item: item[1], reverse=True):
        #     index_i += 1
        #     if index_i < 5:
        #         keywords_snippet[k] = v
        #     else:
        #         keywords_rest[k] = v

        #For each record/ paper bring all the CSO keywords
        CSO_keywords_set = set()
        CSO_keywords_list = []
        CSO_keywords_set.update(candidate["_source"].get("CSO_keywords")['enhanced'])
        CSO_keywords_set.update(candidate["_source"].get("CSO_keywords")['semantic'])
        CSO_keywords_set.update(candidate["_source"].get("CSO_keywords")['syntactic'])
        CSO_keywords_list = list(CSO_keywords_set)


        retrieved_art = Article(
            id=candidate["_id"],
            title=candidate["_source"].get("title"),
            url=url,
            #pdf=pdf,
            snippet=snippet,
            abstract=abstract,
            authors=", ".join(author_details),
            publication_date=candidate["_source"].get("year"),
            #venue=venue,
            #keywords_snippet=keywords_snippet,
            #keywords_rest=keywords_rest,
            #CSO_keywords=candidate["_source"].get("CSO_keywords")['union'],
            CSO_keywords2=CSO_keywords_list,
        )
        candidate_list.append(retrieved_art)

    return candidate_list

def paginate_results(search_result: list, page: int, results_per_page: int = 19):
    paginator = Paginator(search_result, results_per_page)
    try:
        search_result_list = paginator.page(page)
    except PageNotAnInteger:
        search_result_list = paginator.page(1)
    except EmptyPage:
        search_result_list = paginator.page(paginator.num_pages)

    return search_result_list, paginator
