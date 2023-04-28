import json
import requests
from requests import Response

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
empty_cors_config = CORSConfig(
    allow_headers=['RandomHeader']
)
app = APIGatewayRestResolver(cors=empty_cors_config)

@app.get(".+")
def get_handler():
    event: dict = app.current_event
    return {
        'message': 'Hello, CDK! You have hit {}'.format(event['path'])
    }

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
