import os
from aws_lambda_powertools import Logger
from ..helpers.network import APIS, make_request
from ..helpers.datetime import (
    jenkins_build_datetime,
    timedelta_to_string,
)
from ..calculators.shared import (
    FiveHundredError
)

logger = Logger(child=True)

BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "workspace")
BITBUCKET_REPO_SLUG = os.getenv("BITBUCKET_REPO_SLUG", "repo")

def get_num_of_pull_requests():
    num_of_pull_requests_request_url = f"/repositories/{BITBUCKET_WORKSPACE}/{BITBUCKET_REPO_SLUG}/pullrequests?state=MERGED&fields=size"

    num_of_bitbucket_pull_requests_response = make_request(
        APIS.BITBUCKET, num_of_pull_requests_request_url
    )

    if not num_of_bitbucket_pull_requests_response["success"]:
        logger.error(
            "bitbucket request errored out",
            url=num_of_pull_requests_request_url,
            response=num_of_bitbucket_pull_requests_response,
        )
        raise FiveHundredError(response=num_of_bitbucket_pull_requests_response)

    logger.info(
        "successfully got the number of pull requests",
        response=num_of_bitbucket_pull_requests_response,
    )

    try:
        num_of_bitbucket_pull_requests = num_of_bitbucket_pull_requests_response[
            "data"
        ]["size"]
    except KeyError as err:
        raise FiveHundredError(f"Key {str(err)} cannot be found in the dict")

    return num_of_bitbucket_pull_requests


def get_all_pull_requests(number_of_pull_requests):
    pagelen = min(50, number_of_pull_requests)
    all_pull_requests_url = f"/repositories/{BITBUCKET_WORKSPACE}/{BITBUCKET_REPO_SLUG}/pullrequests?state=MERGED&pagelen={pagelen}&fields=values.source.branch,values.id,values.title,values.state,values.merge_commit.hash,values.merge_commit.date,values.merge_commit.links.self.href,values.merge_commit.links.statuses.href,values.merge_commit.parents,values.merge_commit.parents.hash,values.merge_commit.parents.date,values.merge_commit.parents.links.self.href,values.merge_commit.parents.links.html.href,values.merge_commit.parents.links.statuses.href"

    all_pull_request_response = make_request(APIS.BITBUCKET, all_pull_requests_url)

    if not all_pull_request_response["success"]:
        logger.error(
            "bitbucket request errored out",
            url=all_pull_requests_url,
            response=all_pull_request_response,
        )
        raise FiveHundredError(response=all_pull_request_response)

    logger.info(
        "successfully got all of the pull requests",
        response=all_pull_request_response,
    )

    try:
        return all_pull_request_response["data"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")