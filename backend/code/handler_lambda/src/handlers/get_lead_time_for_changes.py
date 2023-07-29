import os
import json
from datetime import timedelta
from aws_lambda_powertools import Logger
from requests import status_codes
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent

from ..calculators.lead_time_for_changes import calculate_lead_time_for_changes
from ..calculators.shared import FiveHundredError, JenkinsHistoryLimit
from ..helpers.network import make_request, APIS
from ..helpers.datetime import timedelta_to_string

BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "workspace")


logger = Logger(child=True)


def get_lead_time_for_changes_handler(global_variables):
    pull_requests_request_url = f"""/repositories/{BITBUCKET_WORKSPACE}/{global_variables["BITBUCKET_REPO_SLUG"]}/pullrequests?state=MERGED&fields=values.id,values.title,values.state,values.merge_commit.hash,values.merge_commit.date,values.merge_commit.links.self.href,values.merge_commit.links.statuses.href,values.merge_commit.parents,values.merge_commit.parents.hash,values.merge_commit.parents.date,values.merge_commit.parents.links.self.href,values.merge_commit.parents.links.html.href,values.merge_commit.parents.links.statuses.href"""

    bitbucket_pull_requests_response = make_request(
        APIS.BITBUCKET, pull_requests_request_url
    )

    if not bitbucket_pull_requests_response["success"]:
        logger.info(
            "bitbucket request errored out",
            url=pull_requests_request_url,
            response=bitbucket_pull_requests_response,
        )
        raise FiveHundredError(response=bitbucket_pull_requests_response)

    logger.debug(
        "successfully got the pull requests response",
        response=bitbucket_pull_requests_response,
    )

    try:
        pull_requests = bitbucket_pull_requests_response["data"]["values"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    lead_time_for_changes = []
    for pull_request in pull_requests:
        try:
            lead_time_for_changes.append(
                calculate_lead_time_for_changes(global_variables, pull_request)
            )
        except JenkinsHistoryLimit:
            break

    average_lead_time_for_changes = sum(lead_time_for_changes) / len(
        lead_time_for_changes
    )

    return Response(
        status_code=status_codes.codes.OK,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(
            {
                "meanDurationInSeconds": average_lead_time_for_changes,
                "meanDurationInDuration": timedelta_to_string(
                    timedelta(seconds=average_lead_time_for_changes)
                ),
            }
        ),
    )
