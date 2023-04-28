from __future__ import annotations
import os
import json
from typing_extensions import TypedDict, NotRequired
from datetime import datetime, timezone
import requests
from requests import Response
from requests.auth import HTTPBasicAuth
from requests.exceptions import JSONDecodeError, RequestException
from enum import Enum
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

JENKINS_API_URL = os.getenv("JENKINS_API_URL", "url")
JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "job")
BITBUCKET_API_URL = os.getenv("BITBUCKET_API_URL", "url")
BITBUCKET_API_USER_NAME = os.getenv("BITBUCKET_API_USER_NAME", "username")
BITBUCKET_API_APP_PASSWORD = os.getenv("BITBUCKET_API_APP_PASSWORD", "password")

bitbucket_auth = HTTPBasicAuth(BITBUCKET_API_USER_NAME, BITBUCKET_API_APP_PASSWORD)

logger = Logger()
empty_cors_config = CORSConfig(allow_headers=["RandomHeader"])
app = APIGatewayRestResolver(cors=empty_cors_config)


class APIS(Enum):
    JENKINS = JENKINS_API_URL
    BITBUCKET = BITBUCKET_API_URL


class RequestResponse(TypedDict):
    success: bool
    statusCode: NotRequired[int | None]
    data: NotRequired[dict | None]


def make_request(api: APIS, path: str) -> RequestResponse:
    return_value: RequestResponse
    if path[0] != "/":
        raise ValueError("invalid path")
    try:
        if api == APIS.JENKINS:
            response = requests.get(f"{JENKINS_API_URL}{path}")
        elif api == APIS.BITBUCKET:
            response = requests.get(f"{BITBUCKET_API_URL}{path}", auth=bitbucket_auth)
    except RequestException as err:
        logger.error(err)
        return_value = {"success": False}
        return return_value

    try:
        if response.ok:
            return_value = {
                "statusCode": response.status_code,
                "success": True,
                "data": response.json(),
            }
            return return_value
        else:
            return_value = {"statusCode": response.status_code, "success": False}
            return return_value
    except JSONDecodeError as err:
        logger.error(err)
        return_value = {"statusCode": response.status_code, "success": False}
        return return_value


def jenkins_build_datetime(jenkins_build) -> datetime:
    return datetime.fromtimestamp(jenkins_build["timestamp"] / 1000.0, timezone.utc)


def calculate_deployment_frequency(jenkins_api_response: dict):
    try:
        main_jenkins_job_list = [
            job for job in jenkins_api_response["jobs"] if job["name"] == "main"
        ]
        if len(main_jenkins_job_list) > 1:
            return {
                "success": False,
                "message": "unexpected number of sub jobs with name main for job in jenkins",
            }
        main_jenkins_job = main_jenkins_job_list[0]
        successful_builds_from_jenkins_job = [
            build
            for build in main_jenkins_job["builds"]
            if build["result"] == "SUCCESS"
        ]
        number_of_deployments = len(successful_builds_from_jenkins_job)
        latest_build_datetime = jenkins_build_datetime(
            successful_builds_from_jenkins_job[0]
        )
        first_build_datetime = jenkins_build_datetime(
            successful_builds_from_jenkins_job[-1]
        )
        time_delta_between_latest_and_first_build = (
            latest_build_datetime - first_build_datetime
        )
        if time_delta_between_latest_and_first_build.days > 0:
            days_between_latest_and_first_build = (
                time_delta_between_latest_and_first_build.days
            )
        else:
            return {
                "success": False,
                "message": "unexpected duration between latest and first build of the job in jenkins",
            }
        return {
            "success": True,
            "data": {
                "numberOfDeployments": number_of_deployments,
                "latestBuildDatetime": latest_build_datetime.isoformat(),
                "firstBuildDatetime": first_build_datetime.isoformat(),
                "daysBetweenLatestAndFirstBuild": days_between_latest_and_first_build,
            },
            "message": "deployment frequency successfully calculated",
        }

    except KeyError:
        return {"success": False}


@app.get("/deployment-frequency")
def get_jenkins():
    event: dict = app.current_event

    response = make_request(
        APIS.JENKINS,
        f"{JENKINS_JOB_NAME}/api/json?tree=jobs[name,color,builds[url,result,timestamp]]",
    )

    logger.info("jenkins request made", {"response": response})

    if response["success"]:
        deployment_frequency = calculate_deployment_frequency(response["data"])
        logger.info(
            "deployment frequency calculated",
            {"deploymentFrequency": deployment_frequency["data"]},
        )
        return {
            "data": deployment_frequency["data"],
            "message": deployment_frequency["message"],
            "request_path": event["path"],
        }
    else:
        return {
            "message": f'request to jenkins unsuccessful. status code: {response["statusCode"]}',
            "request_path": event["path"],
        }


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


@app.get(".+")
def get_handler():
    event: dict = app.current_event
    return {"message": "Hello, CDK! You have hit {}".format(event["path"])}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
