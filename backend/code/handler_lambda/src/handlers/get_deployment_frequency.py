import os
import json
from aws_lambda_powertools import Logger
from requests import status_codes
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent

from ..calculators.deployment_frequency import calculate_deployment_frequency
from ..helpers.network import make_request, APIS

from ..exceptions import FiveHundredError

logger = Logger(child=True)


def get_deployment_frequency_handler(global_variables):
    # for multi branch pipelines
    # /api/json?tree=jobs[name,color,builds[url,result,timestamp]]
    # for single job pipelines
    # /api/json?tree=builds[url,result,timestamp]
    request_url = f"{global_variables['JENKINS_JOB_NAME']}/api/json?tree=allBuilds[url,result,timestamp]"

    logger.debug("making jenkins request", url=request_url)

    response = make_request(APIS.JENKINS, request_url)

    if not response["success"]:
        raise FiveHundredError(response=response)

    logger.debug("jenkins request successfully made", response=response)
    deployment_frequency = calculate_deployment_frequency(response["data"])

    logger.debug(
        "deployment frequency calculated",
        deploymentFrequency=deployment_frequency,
    )
    return Response(
        status_code=status_codes.codes.OK,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(deployment_frequency),
    )
