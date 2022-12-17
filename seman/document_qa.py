from haystack.reader.farm import FARMReader
from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
import requests
import json
import pandas as pd
import time
import logging
from pathlib import Path

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

class DocumentQA:
    """ A class that handles question answering tasks for a set of documents."""

    def __init__(self, model_name_or_path, doc_store_host, index, use_gpu):
        self.reader = FARMReader(model_name_or_path=model_name_or_path, use_gpu=use_gpu)
        self.document_store = ElasticsearchDocumentStore(host=doc_store_host, port=9200, username="", password="", index=index)

    def call_alivecore(self, keyword, facebook_page, twitter_handler, reddit, news_keyword, lang):
        haix_api = "https://alivecore360.com/api/livesearch/v5?key=10df4436-c66a-4259-aad7-aa66f92c4432"
        if facebook_page:
            haix_api = haix_api + "&Facebook_page=" + facebook_page
        if reddit:
            haix_api = haix_api +"&Reddit="+reddit
        if twitter_handler:
            haix_api = haix_api +"&Twitter_handler="+twitter_handler
        if news_keyword:
            haix_api = haix_api +"&news_keyword="+news_keyword
        haix_api = haix_api +"&lang="+lang + "&optional_connectors=livesearch"
        logging.info(f"Alivecore360 Livesearch API: {haix_api}")
        out = requests.get(haix_api)
        self.data = json.loads(out.text)
        logging.info("- - - Initializing - - - ")

        docs_tweets = []
        docs_fb = []
        docs_reddit = []
        docs_news = []
        source_data = {}

        if twitter_handler:
            logging.info("Fetching Twitter Data")
            tweet = []
            sentiment_tweet = []
            publishedTime_tweet = []
            username_tweet = []
            location = []
            followers = []
            statuses_count = []
            handler = []
            id = []
            is_user_verified = []
            #print(self.data["data"]["tweets"]["data"])
            for j in self.data["data"]["tweets"]["data"]:
                try:
                    tweet.append(j["tweet"])
                except:
                    tweet.append("")
                try:
                    publishedTime_tweet.append(j["createdAtISO"])
                except:
                    publishedTime_tweet.append("")
                try:
                    username_tweet.append(j["name"])
                except:
                    username_tweet.append("")
                try:
                    sentiment_tweet.append(j["sentimentPolarity"])
                except:
                    sentiment_tweet.append("")
                try:
                    location.append(j["location"])
                except:
                    location.append("")
                try:
                    followers.append(j["followers"])
                except:
                    followers.append("")
                try:
                    statuses_count.append(j["statuses_count"])
                except:
                    statuses_count.append("")
                try:
                    handler.append(j["handler_name"])
                except:
                    handler.append("")
                try:
                    id.append(j["_id"])
                except:
                    id.append("")
                try:
                    is_user_verified.append(j["is_user_verified"])
                except:
                    is_user_verified.append("")

            for i in range(len(tweet)):
                docs_tweets.append({
                    "text": tweet[i],
                    "meta": {
                        "username": username_tweet[i],
                        "sentiment":sentiment_tweet[i],
                        "published_date":publishedTime_tweet[i],
                        "location": location[i],
                        "followers": followers[i],
                        "statuses_count": statuses_count[i],
                        "handler": handler[i],
                        "is_user_verified": is_user_verified[i],
                        "id": id[i],
                        "complete_text": tweet[i],
                        "handler": twitter_handler,
                        "source": "twitter",
                        "keyword": keyword
                    }
                })
            
            source_data["twitter"] = docs_tweets
            return source_data["twitter"]


        if news_keyword:
            logging.info("Fetching News Articles")
            Title = []
            Sentiment = []
            PublishedTime = []
            link = []
            source = []
            fac_repo = []
            bias = []
            Type = []
            thumbnail = []
            meanSentimentRow = []
            rel_score = []
            for j in self.data["data"]["articles"]["data"]:
                try:
                    Title.append(j["title"])
                except:
                    Title.append("")
                try:
                    PublishedTime.append(j["publishedAt"])
                except:
                    PublishedTime.append("")
                try:
                    link.append(j["url"])
                except:
                    link.append("")
                try:
                    Sentiment.append(j["meanSentimentRow"])
                except:
                    Sentiment.append("")
                try:
                    source.append(j["source"])
                except:
                    source.append("")
                try:
                    fac_repo.append(j["Factual Reporting"])
                except:
                    fac_repo.append("")
                try:
                    bias.append(j["BIAS"])
                except:
                    bias.append("")
                try:
                    Type.append(j["type"]["type"])
                except:
                    Type.append("")
                try:
                    thumbnail.append(j["thumbnail"])
                except:
                    thumbnail.append("")
                try:
                    meanSentimentRow.append(j["meanSentimentRow"])
                except:
                    meanSentimentRow.append("")
                try:
                    rel_score.append(j["Reliability Score"])
                except:
                    rel_score.append("")

            for i in range(len(Title)):
                docs_news.append({
                    "text": Title[i],
                    "meta": {
                        "url": link[i],
                        "sentiment":Sentiment[i],
                        "published_date":PublishedTime[i],
                        "source":source[i],
                        "factual_reporting" :fac_repo[i],
                        "bias" :bias[i],
                        "type": Type[i],
                        "mean_sentiment_row": meanSentimentRow[i],
                        "thumbnail": thumbnail[i],
                        "reliability_score":rel_score[i],
                        "complete_text": Title[i],
                        "handler": news_keyword,
                        "source": "news_articles",
                        "keyword": keyword
                    }
                })
            source_data["news_articles"] = docs_news

        if facebook_page:
            logging.info("Fetching Facebook Data")
            post_caption = []
            comment = []
            PublishedTime = []
            link = []
            sentiment = []
            comment_url = []
            fbHandlerUsed = []
            for j in self.data["data"]["Facebook"]["data"]:
                try:
                    for k in j["comments"]["data"]:
                        try:
                            post_caption.append(k["asReplyToPostMessage"])
                        except:
                            post_caption.append("")
                        try:
                            PublishedTime.append(k["created_time"])
                        except:
                            PublishedTime.append("")
                        try:
                            link.append(k["asReplyToPostLink"])
                        except:
                            link.append("")
                        try:
                            comment.append(k["message"])
                        except:
                            comment.append("")
                        try:
                            sentiment.append(k["sentimentPolarity"])
                        except:
                            sentiment.append("")
                        try:
                            comment_url.append(k["permalink_url"])
                        except:
                            comment_url.append("")
                        try:
                            fbHandlerUsed.append(k["fbHandlerUsed"])
                        except:
                            fbHandlerUsed.append("")
                except:
                    logging.info("No Facebook Comments Found!!")

            for i in range(len(comment)):
                docs_fb.append({
                    "text": comment[i],
                    "meta": {
                        "url": link[i],
                        "post_caption": post_caption[i],
                        "published_date":PublishedTime[i],
                        "sentiment":sentiment[i],
                        "comment_url": comment_url[i],
                        "fb_handler_used": fbHandlerUsed[i],
                        "complete_text": comment[i],
                        "handler": facebook_page,
                        "source": "facebook",
                        "keyword": keyword
                    }
                })
            source_data["facebook"] = docs_fb


        if reddit:
            logging.info("Fetching Reddit")
            comment_id = []
            comments = []
            commentor_username = []
            comment_timestamp = []
            comment_sentiment = []
            post_id = []
            post_title = []
            post_timestamp = []
            post_url = []
            post_score = []
            post_author = []
            post_no_of_ups = []
            post_no_of_downs = []
            post_no_of_likes = []
            post_sentiment = []
            post_num_comments = []
            for j in self.data["data"]["reddit"]["data"]:
                try:
                    for k in j["comments"]:
                        comments.append(k.get("comment",""))
                        comment_id.append(k.get("comment_id",""))
                        commentor_username.append(k.get("commentor_username",""))
                        comment_timestamp.append(k.get("timestamp",""))
                        comment_sentiment.append(k.get("sentimentPolarity",""))
                        post_id.append(j.get("post_id",""))
                        post_title.append(j.get("post_title",""))
                        post_url.append(j.get("post_url",""))
                        post_timestamp.append(j.get("post_timestamp",""))
                        post_score.append(j.get("post_score",""))
                        post_author.append(j.get("author",""))
                        post_no_of_ups.append(j.get("no_of_ups",""))
                        post_no_of_downs.append(j.get("no_of_downs",""))
                        post_no_of_likes.append(j.get("no_of_likes",""))
                        post_sentiment.append(j.get("post_score",""))
                        post_num_comments.append(j.get("num_comments",""))
                except:
                    logging.info("No Reddit Comments Found")

            for i in range(len(comments)):
                docs_reddit.append({
                    "text": comments[i],
                    "meta": {
                        "complete_text": comments[i],
                        "comment_id": comment_id[i],
                        "comment": comments[i],
                        "commenter_username": commentor_username[i],
                        "comment_timestamp": comment_timestamp[i],
                        "comment_sentiment": comment_sentiment[i],
                        "post_id": post_id[i],
                        "post_title": post_title[i],
                        "post_timestamp": post_timestamp[i],
                        "post_url": post_url[i],
                        "post_score": post_score[i],
                        "post_author": post_author[i],
                        "post_no_of_ups": post_no_of_ups[i],
                        "post_no_of_downs": post_no_of_downs[i],
                        "post_no_of_likes": post_no_of_likes[i],
                        "post_sentiment": post_sentiment[i],
                        "post_num_comments": post_num_comments[i],
                        "handler": reddit,
                        "source": "reddit",
                        "keyword": keyword
                    }
                })
            source_data["reddit"] = docs_reddit
        