from os import getenv
from dotenv import load_dotenv

load_dotenv()

config = {
	"google_api_key": f"{getenv('GOOGLE_API_KEY')}",
	"youtube_playlist_id": "PLLALQuK1NDriLbqidWbTYavxdFAAxAMVo",
	"kafka": {
		"bootstrap.servers": "pkc-mxqvx.europe-southwest1.gcp.confluent.cloud:9092",
		"security.protocol": "sasl_ssl",
		"sasl.mechanism": "PLAIN",
		"sasl.username": f"{getenv(SASL_USERNAME)}",
		"sasl.password": f"{getenv(SASL_PASSWORD)}",
	},
	"schema_registry": {
		"url": "https://psrc-do01d.eu-central-1.aws.confluent.cloud",
		"basic.auth.user.info": f"{getenv(USER_INFO)}",
	}
}