import os
import json
from aws_lambda_powertools import Logger
from requests import status_codes
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent

from ..calculators.lead_time_for_changes import calculate_lead_time_for_changes
from ..helpers.network import make_request, APIS

BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "workspace")
BITBUCKET_REPO_SLUG = os.getenv("BITBUCKET_REPO_SLUG", "repo")

logger = Logger(child=True)

def get_lead_time_for_changes_handler(event: APIGatewayProxyEvent):
    pull_requests_request_url = f"""/repositories/{BITBUCKET_WORKSPACE}/{BITBUCKET_REPO_SLUG}/pullrequests?state=MERGED&fields=values.id,values.title,values.state,values.merge_commit.hash,values.merge_commit.date,values.merge_commit.links.self.href,values.merge_commit.links.statuses.href,values.merge_commit.parents,values.merge_commit.parents.hash,values.merge_commit.parents.date,values.merge_commit.parents.links.self.href,values.merge_commit.parents.links.html.href,values.merge_commit.parents.links.statuses.href"""

    bitbucket_pull_requests_response = make_request(
        APIS.BITBUCKET, pull_requests_request_url
    )

    if not bitbucket_pull_requests_response["success"]:
        logger.info(
            "bitbucket request errored out",
            url=pull_requests_request_url,
            response=bitbucket_pull_requests_response,
        )
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body={
                "message": bitbucket_pull_requests_response["message"]
                if "message" in bitbucket_pull_requests_response
                and bitbucket_pull_requests_response["message"]
                else "Error: a problem occured",
                "request_path": "/path",
            },
        )

    logger.debug(
        "successfully got the pull requests response",
        response=bitbucket_pull_requests_response,
    )

    try:
        most_recent_pull_request = bitbucket_pull_requests_response["data"]["values"][0]
    except KeyError as err:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body={
                "message": f"Key {str(err)} cannot be found in the dict",
            },
        )

    lead_time_changes = calculate_lead_time_for_changes(most_recent_pull_request)

    if not lead_time_changes["success"]:
        return Response(
            status_code=status_codes.codes.SERVER_ERROR,
            content_type=content_types.APPLICATION_JSON,
            body={
                "message": lead_time_changes["message"]
                if "message" in lead_time_changes and lead_time_changes["message"]
                else "Error: a problem occured",
                "request_path": "/path",
            },
        )

    return Response(
        status_code=status_codes.codes.OK,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(lead_time_changes["data"]),
    )
