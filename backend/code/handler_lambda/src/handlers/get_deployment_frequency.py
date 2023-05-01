import os
from aws_lambda_powertools import Logger
from requests import status_codes
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent

from ..calculators.deployment_frequency import calculate_deployment_frequency
from ..helpers.network import make_request, APIS

JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "job")

logger = Logger(child=True)


def get_deployment_frequency_handler(event: APIGatewayProxyEvent):

    request_url = f"{JENKINS_JOB_NAME}/api/json?tree=jobs[name,color,builds[url,result,timestamp]]"

    logger.info(
        "making jenkins request",
        {"url": request_url},
    )

    response = make_request(APIS.JENKINS, request_url)

    if response["success"]:
        logger.info("jenkins request successfully made", {"response": response})
        deployment_frequency = calculate_deployment_frequency(response["data"])
        if deployment_frequency["success"]:
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
            logger.info("failed to calculate deployment frequency")
            return Response(
                status_code=status_codes.codes.SERVER_ERROR,
                content_type=content_types.APPLICATION_JSON,
                body={
                    "message": deployment_frequency["message"]
                    if "message" in deployment_frequency
                    and deployment_frequency["message"]
                    else "Error: a problem occured",
                    "request_path": event["path"],
                },
            )
    else:
        logger.info("jenkins request errored out")
        logger.info(response)
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body={
                "message": response["message"]
                if "message" in response and response["message"]
                else "Error: a problem occured",
                "request_path": event["path"],
            },
        )
