from fastapi import Path, Query, Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
from haystack.retriever.sparse import ElasticsearchRetriever
from haystack.pipeline import ExtractiveQAPipeline
from document_qa import DocumentQA
from elasticsearch import Elasticsearch
import time
import os
import logging
from datetime import date, datetime, timedelta

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
##change this key to make it dynamic
API_KEY = "029a14f4825fe6715fa48c3652d115bf6c5d6868f4dd1c7353941f33513f2ba7"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
        status_code=403, detail="Could not validate credentials | Invalid Api Key"
       )

app = FastAPI(title="Semantic Search Livesearch API", version="0.1")

# comment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

doc_store_host = os.environ.get("ELASTICSEARCHDOCUMENTSTORE_PARAMS_HOST", "localhost")
model_name_or_path=os.environ.get("MODELNAME_OR_PATH", "deepset/roberta-base-squad2")
use_gpu = bool(os.environ.get("USE_GPU", 0))

# change index name in production
document_qa_index = "livesearch"
document_qa_livesearch = DocumentQA(
    model_name_or_path=model_name_or_path, doc_store_host=doc_store_host,
    index=document_qa_index, use_gpu=use_gpu)

es_client = Elasticsearch(
    [doc_store_host],
    scheme="http",
    port=9200,
)

# change index name in production
qa_history_index = "qa-history"
if not es_client.indices.exists(index=qa_history_index):
    es_client.indices.create(index=qa_history_index)

@app.get("/semantic-search/livesearch/status")
def get_status(username: str, api_key: APIKey = Depends(get_api_key)):
# def get_status(username: str):
    return {"message": "Api is running"}

@app.get("/semantic-search/livesearch")
def get_livesearch_data(
    keyword: str, Facebook_page: str = Query(None), Twitter_handler: str = Query(None),
    Reddit: str = Query(None), news_keyword: str = Query(None), lang: str = Query(...),
    username: str = Query(...),
    api_key: APIKey = Depends(get_api_key)
    ):
    """
    Calls the alivecore livesearch api for the given sources, stores the data in the document store
    and returns the available sources
    """
    facebook_page = Facebook_page
    twitter_handler = Twitter_handler
    reddit = Reddit

    if facebook_page:
        filters = {
            "handler": [facebook_page],
            "source": ["facebook"]
        }
        document_qa_livesearch.document_store.delete_all_documents(filters=filters)
    if twitter_handler:
        filters = {
            "handler": [twitter_handler],
            "source": ["twitter"]
        }
        document_qa_livesearch.document_store.delete_all_documents(filters=filters)
    if reddit:
        filters = {
            "handler": [reddit],
            "source": ["reddit"]
        }
        document_qa_livesearch.document_store.delete_all_documents(filters=filters)
    if news_keyword:
        filters = {
            "handler": [news_keyword],
            "source": ["news_articles"]
        }
        document_qa_livesearch.document_store.delete_all_documents(filters=filters)

    try:
        alivecore_api_resp = document_qa_livesearch.call_alivecore(keyword, facebook_page, twitter_handler, reddit, news_keyword, lang)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Data not retrieved"
        )
    
    
    sources_available = []
    print("alivecore_api_resp.keys()")
    #print(alivecore_api_resp)
    if alivecore_api_resp!= None:  
        for source in alivecore_api_resp:
            logging.info(source)
            #logging.info(f"Source: {source} - Count: {len(alivecore_api_resp[source])}")
            if len(source) != None:
                document_qa_livesearch.document_store.write_documents(source)
                print ('source')
                if source:
                    sources_available.append(source)

    result = {}
    
    result['sources_available'] = sources_available
    return result

@app.get("/semantic-search/livesearch/answers")
def get_answers(
    question:str, handler: str, source: str,
    username: str = Query(...),
    api_key: APIKey = Depends(get_api_key)
    ):
    """
    Retrieves answers, given a question and a source, from the livesearch data and logs the responses
    """
    filters = {
        "handler": [handler],
        "source": [source]
    }

    # Filter to search for the last 7 days of facebook data as without it ...
    # the pipeline retrieves data in the previous month even though there is enough data in the current month
    if source == "facebook":
        start_date = date.today() - timedelta(7)
        filters["published_date"] = start_date.strftime("%Y-%m-%d")
        custom_query = """
        {
            "query": {
                "bool": {
                    "should": [{"multi_match": {
                        "query": ${query},
                        "type": "most_fields",
                        "fields": ["text"]
                    }}],
                    "filter": [
                        {"terms": {"handler": ${handler}}},
                        {"terms": {"source": ${source}}},
                        {"range": {"published_date": {"gte": ${published_date}}}}
                    ]
                }
            }
        }
        """
        retriever = ElasticsearchRetriever(document_store=document_qa_livesearch.document_store, custom_query=custom_query)
    elif source == "reddit":
        start_date = date.today() - timedelta(7)
        print(start_date.strftime("%Y-%m-%d"))
        filters["comment_timestamp"] = start_date.strftime("%Y-%m-%d")
        custom_query = """
        {
            "query": {
                "bool": {
                    "should": [{"multi_match": {
                        "query": ${query},
                        "type": "most_fields",
                        "fields": ["text"]
                    }}],
                    "filter": [
                        {"terms": {"handler": ${handler}}},
                        {"terms": {"source": ${source}}},
                        {"range": {"comment_timestamp": {"gte": ${comment_timestamp}}}}
                    ]
                }
            }
        }
        """
        retriever = ElasticsearchRetriever(document_store=document_qa_livesearch.document_store, custom_query=custom_query)
    else:
        retriever = ElasticsearchRetriever(document_store=document_qa_livesearch.document_store)


    pipe = ExtractiveQAPipeline(document_qa_livesearch.reader, retriever)

    number_of_retreivers = 15
    number_of_answers = 5
    result = pipe.run(
        query=question,
        top_k_retriever=int(number_of_retreivers),
        top_k_reader=int(number_of_answers),
        filters = filters
    )
    dup_ans = []
    ans = []
    if result['answers']:
        for i in result['answers']:
            if i['meta']['complete_text'] not in dup_ans:
                dup_ans.append(i['meta']['complete_text'])
                ans.append(i)
        result['answers'] = ans

    qa_history_es_doc = {
        "question": question,
        "answers": result["answers"],
        "handler": handler,
        "source": source,
        "username": username,
        "created_at": datetime.now()
    }
    es_client.index(qa_history_index, body=qa_history_es_doc)

    return result

@app.get("/semantic-search/livesearch/qa-history")
def get_qa_history(
    latest_k: int = Query(10, gt=0), username: str = Query(...),
    api_key: APIKey = Depends(get_api_key)
    ):
    """
    Retrieves the latest 'k' questions asked along with the corresponding answers for a given user
    """
    body = {
        "size": latest_k,
        "sort": { "created_at": "desc"},
        "query": {
            "bool": {
                "must": {
                    "match_all": {}
                },
                "filter": {
                    "terms": {
                        "username.keyword": [username]
                    }
                }
            }
        }
    }
    results = es_client.search(index=qa_history_index, body=body)

    query_history_results = []
    for result in results["hits"]["hits"]:
        query_history_results.append(result["_source"])
    return query_history_results

@app.get("/semantic-search/livesearch/api-call-count")
def get_api_call_count(username: str = Query(...), api_key: APIKey = Depends(get_api_key)):
    """
    Returns the number of api calls for a given user
    """
    results = es_client.count(index=qa_history_index, q=f"username.keyword:{username}")
    return {"count": results["count"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
