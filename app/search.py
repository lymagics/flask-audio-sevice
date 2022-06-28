import os
from urllib.parse import urlparse

from elasticsearch import Elasticsearch
from flask import current_app


def init_search(config_name):
    """Initialize elasticsearch depending on config.
    
    :param config_name: name of config current app build on.
    """
    url_search = os.environ.get("ELASTICSEARCH_URL")
    if url_search:
        if config_name == "development" or config_name == "default":
            return Elasticsearch(url_search)
        if config_name == "production":
            url = urlparse(url_search)
            return Elasticsearch(
                [f"{url.scheme}://{url.hostname}:443"],
                http_auth=(url.username, url.password)
            )
    return None


def add_to_index(index, model):
    """Append index to elasticserch engine.
    
    :param index: index to append.
    :param model: add model field to index.
    """
    if current_app.elasticsearch is None:
        return 
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id,
                                    body=payload)


def remove_from_index(index, model):
    """Delete index from elasticsearch engine.
    
    :param index: index to delete.
    :param model: delete model field from index.
    """
    if current_app.elasticsearch is None:
        return 
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    """Query to elasticsearch engine.
    
    :param index: index to query.
    :param query: query to execute.
    :param page: current pagination page.
    :param per_page: amount of per page items.
    """
    if current_app.elasticsearch is None:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"]
                }
            },
            "from": (page-1)*per_page,
            "size": per_page
        }
    )
    ids = [int(hits["_id"]) for hits in search["hits"]["hits"]]
    return ids, search["hits"]["total"]["value"]


def create_index(index):
    """Create index.
    
    "param index: index to create.
    """
    try:
        current_app.elasticsearch.indices.create(index)
    except:
        pass
