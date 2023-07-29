import json
from aws_lambda_powertools import Logger
from requests import status_codes
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent

from ..calculators.shared import get_all_pull_requests, get_num_of_pull_requests
from ..exceptions import FiveHundredError


logger = Logger(child=True)


def get_change_failure_rate_handler(global_variables):
    num_of_bitbucket_pull_requests = get_num_of_pull_requests(global_variables)

    pull_requests_response = get_all_pull_requests(
        global_variables, num_of_bitbucket_pull_requests
    )

    change_failure_count = 0
    pull_requests = []

    try:
        pull_requests = pull_requests_response["values"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    for pull_request in pull_requests[:-1]:
        try:
            source_branch = pull_request["source"]["branch"]["name"]
        except KeyError as err:
            raise FiveHundredError(
                message=f"Key {str(err)} cannot be found in the dict"
            )

        if "hotfix" in source_branch:
            change_failure_count += 1

    return Response(
        status_code=status_codes.codes.OK,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(
            {
                "percentageOfChangeFailures": int(
                    (change_failure_count / len(pull_requests)) * 100
                )
            }
        ),
    )
