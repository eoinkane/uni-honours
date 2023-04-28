import os
import requests
from requests import Response
from requests.exceptions import JSONDecodeError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

JENKINS_API_URL = os.getenv('JENKINS_API_URL', 'url')

logger = Logger()
empty_cors_config = CORSConfig(
    allow_headers=['RandomHeader']
)
app = APIGatewayRestResolver(cors=empty_cors_config)

@app.get('/jenkins-test')
def get_jenkins():
    event: dict = app.current_event
    response = requests.get(f'{JENKINS_API_URL}/api/json')

    if response.ok:
        try:
            return {
                'data': response.json()["jobs"][0],
                'message': f'request to jenkins successful status code: {response.status_code}',
                'request_path': event['path']
            }
        except JSONDecodeError as err:
            logger.error(err)
            return {
                'message': f'request to jenkins unsuccessful. status code: {response.status_code}',
                'request_path': event['path']
            }
    return {
        'message': f'request to jenkins unsuccessful. status code: {response.status_code}',
        'request_path': event['path']
    }

@app.get(".+")
def get_handler():
    event: dict = app.current_event
    return {
        'message': 'Hello, CDK! You have hit {}'.format(event['path'])
    }

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
