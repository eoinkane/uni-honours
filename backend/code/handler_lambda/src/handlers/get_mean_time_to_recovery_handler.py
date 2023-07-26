import os
import json
from datetime import timedelta
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayProxyEvent
from requests import status_codes
from ..helpers.network import APIS, make_request
from ..helpers.datetime import (
    jenkins_build_datetime,
    timedelta_to_string,
)
from ..calculators.shared import (
    FiveHundredError,
    JenkinsHistoryLimit,
)

from ..calculators.mean_time_to_recovery import (
    filter_out_hotfix_pull_requests,
    get_timestamp_of_pr_build_of_pull_request,
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

    return all_pull_request_response["data"]


def get_mean_time_to_recovery_handler(event: APIGatewayProxyEvent):
    num_of_bitbucket_pull_requests = get_num_of_pull_requests()

    pull_requests_response = get_all_pull_requests(num_of_bitbucket_pull_requests)

    pull_requests = []

    try:
        pull_requests = pull_requests_response["values"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    filtered_pull_request_with_non_hotfixes = filter_out_hotfix_pull_requests(
        pull_requests
    )

    time_to_recoverys = []

    for pull_request in filtered_pull_request_with_non_hotfixes:
        try:
            jenkins_pr_build_of_current_pull_request_finish_timestamp = (
                get_timestamp_of_pr_build_of_pull_request(pull_request)
            )
        except JenkinsHistoryLimit:
            break

        jenkins_pr_build_of_current_pull_request_finish_datetime = (
            jenkins_build_datetime(
                {"timestamp": jenkins_pr_build_of_current_pull_request_finish_timestamp}
            )
        )

        if pull_request == filtered_pull_request_with_non_hotfixes[0]:
            finish_datetime_one = (
                jenkins_pr_build_of_current_pull_request_finish_datetime
            )
            continue

        finish_datetime_two = jenkins_pr_build_of_current_pull_request_finish_datetime

        duration: timedelta = finish_datetime_one - finish_datetime_two

        time_to_recoverys.append(duration.total_seconds())

        finish_datetime_one = finish_datetime_two

    mean_time_to_recovery_seconds = sum(time_to_recoverys) / len(time_to_recoverys)

    mean_time_to_recovery_timedelta = timedelta(seconds=mean_time_to_recovery_seconds)

    return Response(
        status_code=status_codes.codes.OK,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps(
            {
                "meanTimeToRecoverySeconds": mean_time_to_recovery_seconds,
                "meanTimeToRecoveryDurations": timedelta_to_string(
                    mean_time_to_recovery_timedelta
                ),
            }
        ),
    )