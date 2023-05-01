from __future__ import annotations
import os
from typing_extensions import TypedDict, NotRequired
from enum import Enum
import requests
from requests import Response, status_codes
from requests.auth import HTTPBasicAuth
from requests.exceptions import JSONDecodeError, RequestException
from aws_lambda_powertools import Logger

JENKINS_API_URL = os.getenv("JENKINS_API_URL", "url")
JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "job")
BITBUCKET_API_URL = os.getenv("BITBUCKET_API_URL", "url")
BITBUCKET_API_USER_NAME = os.getenv("BITBUCKET_API_USER_NAME", "username")
BITBUCKET_API_APP_PASSWORD = os.getenv("BITBUCKET_API_APP_PASSWORD", "password")

bitbucket_auth = HTTPBasicAuth(BITBUCKET_API_USER_NAME, BITBUCKET_API_APP_PASSWORD)

logger = Logger(child=True)


class APIS(Enum):
    JENKINS = JENKINS_API_URL
    BITBUCKET = BITBUCKET_API_URL


class RequestResponse(TypedDict):
    success: bool
    statusCode: NotRequired[int | None]
    message: NotRequired[str | None]
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
            return_value = {
                "statusCode": response.status_code,
                "message": response.text,
                "success": False,
            }
            return return_value
    except JSONDecodeError as err:
        logger.error(err)
        return_value = {"statusCode": response.status_code, "success": False}
        return return_value
