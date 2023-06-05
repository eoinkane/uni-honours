from __future__ import annotations
import os
from typing_extensions import TypedDict, NotRequired
from aws_lambda_powertools import Logger
from ..helpers.network import APIS, make_request, RequestResponse
from ..helpers.datetime import jenkins_build_datetime

logger = Logger(child=True)

BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "workspace")
BITBUCKET_REPO_SLUG = os.getenv("BITBUCKET_REPO_SLUG", "repo")

JENKINS_AT_JOB_NAME = os.getenv("JENKINS_AT_JOB_NAME", "job")
JENKINS_PR_JOB_NAME = os.getenv("JENKINS_PR_JOB_NAME", "job")

class SingularChangeLeadTimeData(TypedDict):
    # numberOfDeployments: str
    # latestBuildDatetime: str
    # firstBuildDatetime: str
    # daysBetweenLatestAndFirstBuild: int
    no: str


class SingularChangeLeadTimeResult(TypedDict):
    success: bool
    message: NotRequired[str | None]
    data: NotRequired[SingularChangeLeadTimeData | None]


def create_error_singular_change_lead_time_result(
    message: str,
) -> SingularChangeLeadTimeResult:
    return SingularChangeLeadTimeResult({"success": False, "message": message})


def build_failed_network_request_error_message(api: APIS):
    api_enum = APIS(api)
    if "JENKINS" in api_enum.name:
        return "jenkins"
    elif "BITBUCKET" in api_enum.name:
        return "bitbucket"
    else:
        return ""


def handle_failed_network_request(api: APIS, url: str, response: RequestResponse):
    logger.error(
        build_failed_network_request_error_message(api), url=url, response=response
    )
    return SingularChangeLeadTimeResult(
        {
            "success": False,
            "message": response["message"]
            if "message" in response and response["message"]
            else "Error: a network request failed",
        }
    )


def extract_status_of_parent_commit_url(pull_request):
    parent_commit_hash = pull_request["merge_commit"]["parents"][0]["hash"]
    parent_commit_hash_url = pull_request["merge_commit"]["parents"][0]["links"][
        "html"
    ]["href"]
    statuses_of_parent_commit_url = pull_request["merge_commit"]["parents"][0]["links"][
        "statuses"
    ]["href"]

    return parent_commit_hash, parent_commit_hash_url, statuses_of_parent_commit_url


def fetch_last_build_of_parent_commit_display_url(
    statuses_of_parent_commit_url: str,
) -> RequestResponse:
    statuses_of_parent_commit_specific_fields_url = f"{statuses_of_parent_commit_url}?fields=values.key,values.type,values.state,values.name,values.url"

    logger.debug(
        "making request to get the statuses of the commit before the most recent PR",
        url=statuses_of_parent_commit_specific_fields_url,
    )

    statuses_of_parents_commit_response = make_request(
        APIS.DIRECT_BITBUCKET, statuses_of_parent_commit_specific_fields_url
    )

    if not statuses_of_parents_commit_response["success"]:
        return handle_failed_network_request(
            APIS.DIRECT_BITBUCKET,
            statuses_of_parent_commit_specific_fields_url,
            statuses_of_parents_commit_response,
        )

    logger.debug(
        "successful request to bitbucket to get the statuses",
        url=statuses_of_parent_commit_specific_fields_url,
        response=statuses_of_parents_commit_response,
    )

    return statuses_of_parents_commit_response


def extract_last_build_of_parent_commit_display_url(
    statuses_of_parents_commit_response: RequestResponse,
) -> str:
    return statuses_of_parents_commit_response["data"]["values"][0]["url"]


def fetch_first_jenkins_build_of_current_pull_request_url(
    last_build_of_parent_commit_display_url: str,
):
    last_build_of_parent_commit_api_url = last_build_of_parent_commit_display_url.replace(
        "/display/redirect",
        "/api/json?tree=displayName,number,id,fullDisplayName,duration,timestamp,url,inProgress,nextBuild[number,url]",
    )

    logger.debug(
        "making request to get the first build of the commit from the most recent PR",
        url=last_build_of_parent_commit_api_url,
    )
    last_build_of_parent_commit_response = make_request(
        APIS.DIRECT_JENKINS, last_build_of_parent_commit_api_url
    )

    if not last_build_of_parent_commit_response["success"]:
        return handle_failed_network_request(
            APIS.DIRECT_JENKINS,
            last_build_of_parent_commit_api_url,
            last_build_of_parent_commit_response,
        )

    logger.debug(
        "successful request to jenkins to get the first build of the commit from the most recent PR",
        url=last_build_of_parent_commit_api_url,
        response=last_build_of_parent_commit_response,
    )

    return last_build_of_parent_commit_response


def extract_first_jenkins_build_of_current_pull_request_url(
    last_build_of_parent_commit_response: RequestResponse,
):
    return last_build_of_parent_commit_response["data"]["nextBuild"]["url"]


def fetch_first_jenkins_build_of_current_pull_request(
    first_jenkins_build_of_current_pull_request_url: str,
):
    first_jenkins_build_of_current_pull_request_apis_url = f"{first_jenkins_build_of_current_pull_request_url}api/json?tree=displayName,number,id,fullDisplayName,duration,timestamp,url,inProgress,nextBuild[number,url]"

    logger.debug(
        "making request to get the the id of the first st build of the commit from the most recent PR",
        url=first_jenkins_build_of_current_pull_request_apis_url,
    )
    first_jenkins_build_of_current_pull_request = make_request(
        APIS.DIRECT_JENKINS, first_jenkins_build_of_current_pull_request_apis_url
    )

    if not first_jenkins_build_of_current_pull_request["success"]:
        return handle_failed_network_request(
            APIS.DIRECT_JENKINS,
            first_jenkins_build_of_current_pull_request_apis_url,
            first_jenkins_build_of_current_pull_request,
        )

    logger.debug(
        "successful request to jenkins to get the the id of the first st build of the commit from the most recent PR",
        url=first_jenkins_build_of_current_pull_request_apis_url,
        response=first_jenkins_build_of_current_pull_request,
    )
    return (
        first_jenkins_build_of_current_pull_request_apis_url,
        first_jenkins_build_of_current_pull_request,
    )


def extract__first_jenkins_build_of_current_pull_request(
    first_jenkins_build_of_current_pull_request: RequestResponse,
):
    first_jenkins_build_of_current_pull_request_id = (
        first_jenkins_build_of_current_pull_request["data"]["id"]
    )
    first_jenkins_build_of_current_pull_request_timestamp = (
        first_jenkins_build_of_current_pull_request["data"]["timestamp"]
    )
    return (
        first_jenkins_build_of_current_pull_request_id,
        first_jenkins_build_of_current_pull_request_timestamp,
    )


def calculate_lead_time_for_changes(pull_request) -> SingularChangeLeadTimeResult:
    # first section
    # takes in the pull_request and outputs 3 variables: parent_commit_hash, parent_commit_hash_url, statuses_of_parent_commit_url
    try:
        (
            parent_commit_hash,
            parent_commit_hash_url,
            statuses_of_parent_commit_url,
        ) = extract_status_of_parent_commit_url(pull_request)
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected number of merge commits parents for PR {pull_request.get('id', 'null')} in {BITBUCKET_REPO_SLUG}"
        )

    # second section
    # takes in 3 variables: parent_commit_hash, parent_commit_hash_url, statuses_of_parent_commit_url
    # outputs: last_build_of_parent_commit_display_url

    statuses_of_parents_commit_response = fetch_last_build_of_parent_commit_display_url(
        statuses_of_parent_commit_url
    )

    try:
        last_build_of_parent_commit_display_url = (
            extract_last_build_of_parent_commit_display_url(
                statuses_of_parents_commit_response
            )
        )
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected number of builds for for commit {parent_commit_hash} in {BITBUCKET_REPO_SLUG}. Visit {parent_commit_hash_url}"
        )

    # third section
    # takes in: last_build_of_parent_commit_display_url
    # outputs first_jenkins_build_of_current_pull_request_url

    last_build_of_parent_commit_response = (
        fetch_first_jenkins_build_of_current_pull_request_url(
            last_build_of_parent_commit_display_url
        )
    )

    try:
        first_jenkins_build_of_current_pull_request_url = (
            extract_first_jenkins_build_of_current_pull_request_url(
                last_build_of_parent_commit_response
            )
        )
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected data from {BITBUCKET_REPO_SLUG} staging job. Visit {last_build_of_parent_commit_display_url}"
        )

    # fourth section
    # takes in first_jenkins_build_of_current_pull_request_url
    # outputs first_jenkins_build_of_current_pull_request_id, first_jenkins_build_of_current_pull_request_timestamp
    #
    (
        first_jenkins_build_of_current_pull_request_apis_url,
        first_jenkins_build_of_current_pull_request,
    ) = fetch_first_jenkins_build_of_current_pull_request(
        first_jenkins_build_of_current_pull_request_url
    )

    try:
        (
            first_jenkins_build_of_current_pull_request_id,
            first_jenkins_build_of_current_pull_request_timestamp,
        ) = extract__first_jenkins_build_of_current_pull_request(
            first_jenkins_build_of_current_pull_request
        )
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected data from {first_jenkins_build_of_current_pull_request_apis_url} in {BITBUCKET_REPO_SLUG} staging job. Visit {first_jenkins_build_of_current_pull_request_apis_url}"
        )

    # fifth section

    first_jenkins_build_of_current_pull_request_datetime = jenkins_build_datetime(
        {"timestamp": first_jenkins_build_of_current_pull_request_timestamp}
    )

    # sixth section
    # takes in first_jenkins_build_of_current_pull_request_id
    # outputs first_jenkins_at_build_of_current_pull_request_id

    first_jenkins_at_build_of_current_pull_request_path = f"{JENKINS_AT_JOB_NAME}/api/xml?tree=builds[number,url,actions[causes[upstreamUrl,upstreamBuild]]]&xpath=/workflowJob/build/action/cause[upstreamBuild%20=%20%27{first_jenkins_build_of_current_pull_request_id}%27]/../.."

    logger.debug(
        "making request to get the the id of the first at build of the commit from the most recent PR",
        path=first_jenkins_at_build_of_current_pull_request_path,
    )
    first_jenkins_at_build_of_current_pull_request = make_request(
        APIS.JENKINS, first_jenkins_at_build_of_current_pull_request_path
    )

    if not first_jenkins_at_build_of_current_pull_request["success"]:
        return handle_failed_network_request(
            APIS.JENKINS,
            first_jenkins_at_build_of_current_pull_request_path,
            first_jenkins_at_build_of_current_pull_request,
        )

    logger.debug(
        "successful request to jenkins to get the the id of the first at build of the commit from the most recent PR",
        path=first_jenkins_at_build_of_current_pull_request_path,
        response=first_jenkins_at_build_of_current_pull_request,
    )

    try:
        first_jenkins_at_build_of_current_pull_request_id = (
            first_jenkins_at_build_of_current_pull_request["data"]["build"]["number"]
        )
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected data from {first_jenkins_at_build_of_current_pull_request_path} in {BITBUCKET_REPO_SLUG} acceptance job. Visit {first_jenkins_at_build_of_current_pull_request_path}"
        )

    # seventh section
    # takes in first_jenkins_at_build_of_current_pull_request_id
    # outputs first_jenkins_pr_build_of_current_pull_request_start_timestamp & first_jenkins_pr_build_of_current_pull_request_duration_seconds

    first_jenkins_pr_build_of_current_pull_request_path = f"{JENKINS_PR_JOB_NAME}/api/xml?tree=builds[duration,timestamp,number,url,actions[causes[upstreamUrl,upstreamBuild]]]&xpath=/workflowJob/build/action/cause[upstreamBuild%20=%20%27{first_jenkins_at_build_of_current_pull_request_id}%27]/../.."

    logger.debug(
        "making request to get the the id of the first prod build of the commit from the most recent PR",
        path=first_jenkins_pr_build_of_current_pull_request_path,
    )
    first_jenkins_pr_build_of_current_pull_request = make_request(
        APIS.JENKINS, first_jenkins_pr_build_of_current_pull_request_path
    )

    if not first_jenkins_pr_build_of_current_pull_request["success"]:
        return handle_failed_network_request(
            APIS.JENKINS,
            first_jenkins_pr_build_of_current_pull_request_path,
            first_jenkins_pr_build_of_current_pull_request,
        )

    logger.debug(
        "successful request to jenkins to",
        path=first_jenkins_pr_build_of_current_pull_request_path,
        response=first_jenkins_pr_build_of_current_pull_request,
    )

    try:
        first_jenkins_pr_build_of_current_pull_request_duration_seconds = int(
            first_jenkins_pr_build_of_current_pull_request["data"]["build"]["duration"]
        )
        first_jenkins_pr_build_of_current_pull_request_start_timestamp = int(
            first_jenkins_pr_build_of_current_pull_request["data"]["build"]["timestamp"]
        )
    except KeyError as err:
        return create_error_singular_change_lead_time_result(
            f"Key {str(err)} cannot be found in the dict"
        )
    except IndexError as err:
        return create_error_singular_change_lead_time_result(
            f"Unexpected data from {first_jenkins_pr_build_of_current_pull_request_path} in {BITBUCKET_REPO_SLUG} production job. Visit {first_jenkins_pr_build_of_current_pull_request_path}"
        )

    # eighth section

    first_jenkins_pr_build_of_current_pull_request_finish_timestamp = (
        first_jenkins_pr_build_of_current_pull_request_start_timestamp
        + first_jenkins_pr_build_of_current_pull_request_duration_seconds
    )

    first_jenkins_pr_build_of_current_pull_request_finish_datetime = jenkins_build_datetime(
        {"timestamp": first_jenkins_pr_build_of_current_pull_request_finish_timestamp}
    )

    logger.info(
        first_jenkins_pr_build_of_current_pull_request_finish_datetime
        - first_jenkins_build_of_current_pull_request_datetime
    )

    return SingularChangeLeadTimeResult(
        {
            "success": True,
            "data": {
                "startTime": first_jenkins_build_of_current_pull_request_datetime.isoformat(),
                "finishTime": first_jenkins_pr_build_of_current_pull_request_finish_datetime.isoformat(),
            },
        }
    )
