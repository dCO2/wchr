import requests
import json
from config import config
from flask import Flask
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serializing_producer import SerializingProducer

app = Flask(__name__)

def fetch_playlist_items_page(google_api_key, youtube_playlist_id, page_token):
	response = requests.get("https://youtube.googleapis.com/youtube/v3/playlistItems", params={
		"key": google_api_key,
		"playlistId": youtube_playlist_id,
		"part": "contentDetails",
		"pageToken": page_token,
	})

	payload = json.loads(response.text)

	return payload

def fetch_playlist_items(google_api_key, youtube_playlist_id, next_page_token=None):
	payload = fetch_playlist_items_page(google_api_key, youtube_playlist_id, next_page_token)

	yield from payload["items"]

	next_page_token = payload.get("nextPageToken")

	if next_page_token is not None:
		yield from fetch_playlist_items(google_api_key, youtube_playlist_id, next_page_token)

def fetch_video_items_page(google_api_key,video_id, page_token):
	response = requests.get("https://youtube.googleapis.com/youtube/v3/videos", params={
		"key": google_api_key,
		"id": video_id,
		"part": "snippet, statistics",
		"pageToken": page_token,
	})

	payload = json.loads(response.text)

	return payload

def fetch_video_items(google_api_key, video_id, next_page_token=None):
	payload = fetch_video_items_page(google_api_key, video_id, next_page_token)

	yield from payload["items"]

	next_page_token = payload.get("nextPageToken")

	if next_page_token is not None:
		yield from fetch_video_items(google_api_key, video_id, next_page_token)

def summarize_video(video):
	return {
		"id": video["id"],
		"title": video["snippet"]["title"],
		"views": int(video["statistics"].get("viewCount", 0)),
		"likes": int(video["statistics"].get("likeCount", 0)),
		"comments": int(video["statistics"].get("commentCount", 0)),
	}

def on_delivery(err, record):
	pass

@app.route("/")
def main():
	google_api_key = config["google_api_key"]
	youtube_playlist_id = config["youtube_playlist_id"]
	# full_playlist_data = {"items": []}
	schema_registry_client = SchemaRegistryClient(config["schema_registry"])
	youtube_videos_value_schema = schema_registry_client.get_latest_version("youtube_videos-value")

	kafka_config = config["kafka"] | {
		"key.serializer": StringSerializer(),
		"value.serializer": AvroSerializer(
			schema_registry_client,
			youtube_videos_value_schema.schema.schema_str,
		),
	}

	producer = SerializingProducer(kafka_config)

	for video_item in fetch_playlist_items(google_api_key, youtube_playlist_id):
		video_id = video_item["contentDetails"]["videoId"]
		for video in fetch_video_items(google_api_key, video_id):

			producer.produce(
				topic="youtube_videos",
				value={
					"TITLE": video["snippet"]["title"],
					"VIEWS": int(video["statistics"].get("viewCount", 0)),
					"LIKES": int(video["statistics"].get("likeCount", 0)),
					"COMMENTS": int(video["statistics"].get("commentCount", 0)),
				},
				key=video_id,
				on_delivery=on_delivery,
			)

	producer.flush()
	return f"<code><b>WCHR</b> is watching <a href=\"https://www.youtube.com/playlist?list={youtube_playlist_id}\">https://www.youtube.com/playlist?list={youtube_playlist_id}</a> for changes.<br>Alerts are sent to the <b>wchr</b> Telegram bot.</code>"

@app.route("/about")
def about():
	return "wchr (pronounced watcher) is a reactive data streaming app"
