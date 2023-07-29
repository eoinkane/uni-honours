from __future__ import annotations
from hashlib import sha1
import os
import json
import requests
from requests import status_codes
from requests.exceptions import JSONDecodeError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    CORSConfig,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler import Response, content_types

from .exceptions import FiveHundredError, FourTwoTwoError
from .handlers.get_lead_time_for_changes import get_lead_time_for_changes_handler
from .handlers.get_deployment_frequency import get_deployment_frequency_handler
from .handlers.get_mean_time_to_recovery_handler import (
    get_mean_time_to_recovery_handler,
)
from .handlers.get_change_failure_rate import get_change_failure_rate_handler
from .globals import validate_project_id_param

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger = Logger(level=LOG_LEVEL)
empty_cors_config = CORSConfig(allow_headers=["RandomHeader"])
app = APIGatewayRestResolver(cors=empty_cors_config)


@app.get("/deployment-frequency/<project_id>")
def get_deployment_frequency_route(project_id: str):
    try:
        global_variables = validate_project_id_param(int(project_id))

        return get_deployment_frequency_handler(global_variables)
    except FourTwoTwoError as err:
        return Response(
            status_code=status_codes.codes.UNPROCESSABLE_ENTITY,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/deployment-frequency"}),
        )
    except FiveHundredError as err:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/deployment-frequency"}),
        )


@app.get("/lead-time-for-changes/<project_id>")
def get_lead_time_for_changes(project_id: str):
    try:
        global_variables = validate_project_id_param(int(project_id))

        return get_lead_time_for_changes_handler(global_variables)
    except FourTwoTwoError as err:
        return Response(
            status_code=status_codes.codes.UNPROCESSABLE_ENTITY,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/lead-time-for-changes"}),
        )
    except FiveHundredError as err:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/lead-time-for-changes"}),
        )


@app.get("/mean-time-to-recovery/<project_id>")
def get_mean_time_to_recovery(project_id: str):
    try:
        global_variables = validate_project_id_param(int(project_id))

        return get_mean_time_to_recovery_handler(global_variables)
    except FourTwoTwoError as err:
        return Response(
            status_code=status_codes.codes.UNPROCESSABLE_ENTITY,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/mean-time-to-recovery"}),
        )
    except FiveHundredError as err:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/mean-time-to-recovery"}),
        )


@app.get("/change-failure-rate/<project_id>")
def get_change_failure_rate(project_id: str):
    try:
        global_variables = validate_project_id_param(int(project_id))

        return get_change_failure_rate_handler(global_variables)
    except FourTwoTwoError as err:
        return Response(
            status_code=status_codes.codes.UNPROCESSABLE_ENTITY,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/change-failure-rate"}),
        )
    except FiveHundredError as err:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({"message": err.message, "path": "/change-failure-rate"}),
        )


@app.get("/json-test")
def get_json_test():
    event: dict = app.current_event
    response = requests.get("https://jsonplaceholder.typicode.com/todos/1")

    if response.ok:
        try:
            return {
                "data": response.json(),
                "message": f"request to json placeholder successful status code: {response.status_code}",
                "request_path": event["path"],
            }
        except JSONDecodeError as err:
            logger.error(err)
            return {
                "message": f"request to json placeholder unsuccessful. status code: {response.status_code}",
                "request_path": event["path"],
            }
    return {
        "message": f"request to json placeholder unsuccessful. status code: {response.status_code}",
        "request_path": event["path"],
    }


@app.get("/echo")
def get_echo():
    return {
        "hash": sha1(
            json.dumps(app.current_event.raw_event, sort_keys=True).encode("utf-8")
        ).hexdigest()
    }


@app.get(".+")
def get_handler():
    event: dict = app.current_event
    return {"message": "Hello, CDK! You have hit {}".format(event["path"])}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
