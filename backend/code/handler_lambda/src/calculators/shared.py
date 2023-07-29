import os
import json
from aws_lambda_powertools import Logger
from ..helpers.network import APIS, make_request, RequestResponse

logger = Logger(child=True)

BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "workspace")
from ..exceptions import FiveHundredError, JenkinsHistoryLimit


def extract_status_of_parent_commit_url(pull_request):
    parent_commit_hash = pull_request["merge_commit"]["parents"][0]["hash"]
    parent_commit_hash_url = pull_request["merge_commit"]["parents"][0]["links"][
        "html"
    ]["href"]
    statuses_of_parent_commit_url = pull_request["merge_commit"]["parents"][0]["links"][
        "statuses"
    ]["href"]

    return parent_commit_hash, parent_commit_hash_url, statuses_of_parent_commit_url


def get_num_of_pull_requests(global_variables):
    num_of_pull_requests_request_url = f"/repositories/{BITBUCKET_WORKSPACE}/{global_variables['BITBUCKET_REPO_SLUG']}/pullrequests?state=MERGED&fields=size"

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

    logger.debug(
        "successfully got the number of pull requests",
        response=num_of_bitbucket_pull_requests_response,
    )

    try:
        num_of_bitbucket_pull_requests = num_of_bitbucket_pull_requests_response[
            "data"
        ]["size"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    return num_of_bitbucket_pull_requests


def get_all_pull_requests(global_variables, number_of_pull_requests):
    pagelen = min(50, number_of_pull_requests)
    all_pull_requests_url = f"/repositories/{BITBUCKET_WORKSPACE}/{global_variables['BITBUCKET_REPO_SLUG']}/pullrequests?state=MERGED&pagelen={pagelen}&fields=values.source.branch,values.id,values.title,values.state,values.merge_commit.hash,values.merge_commit.date,values.merge_commit.links.self.href,values.merge_commit.links.statuses.href,values.merge_commit.parents,values.merge_commit.parents.hash,values.merge_commit.parents.date,values.merge_commit.parents.links.self.href,values.merge_commit.parents.links.html.href,values.merge_commit.parents.links.statuses.href"

    all_pull_request_response = make_request(APIS.BITBUCKET, all_pull_requests_url)

    if not all_pull_request_response["success"]:
        logger.error(
            "bitbucket request errored out",
            url=all_pull_requests_url,
            response=all_pull_request_response,
        )
        raise FiveHundredError(response=all_pull_request_response)

    logger.debug(
        "successfully got all of the pull requests",
        response=all_pull_request_response,
    )

    return all_pull_request_response["data"]


def extract_parent_commits(global_variables, pull_request):
    try:
        (
            parent_commit_hash,
            parent_commit_hash_url,
            statuses_of_parent_commit_url,
        ) = extract_status_of_parent_commit_url(pull_request)
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            f"Unexpected number of merge commits parents for PR {pull_request.get('id', None)} in {global_variables['BITBUCKET_REPO_SLUG']}"
        )

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
        raise FiveHundredError(response=statuses_of_parents_commit_response)

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


def fetch_parent_commit_statuses(
    global_variables,
    parent_commit_hash,
    parent_commit_hash_url,
    statuses_of_parent_commit_url,
):
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
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            f"Unexpected number of builds for for commit {parent_commit_hash} in {global_variables['BITBUCKET_REPO_SLUG']}. Visit {parent_commit_hash_url}"
        )

    return last_build_of_parent_commit_display_url


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
        raise FiveHundredError(response=last_build_of_parent_commit_response)

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


def get_last_build_of_parent_commit(
    global_variables, last_build_of_parent_commit_display_url
):
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
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            f"Unexpected data from {global_variables['BITBUCKET_REPO_SLUG']} staging job. Visit {last_build_of_parent_commit_display_url}"
        )

    return first_jenkins_build_of_current_pull_request_url


def fetch_first_jenkins_build_of_current_pull_request(
    global_variables,
    first_jenkins_build_of_current_pull_request_url: str,
):
    first_jenkins_build_of_current_pull_request_apis_url = f"{first_jenkins_build_of_current_pull_request_url}api/json?tree=displayName,result,number,id,fullDisplayName,duration,timestamp,url,inProgress,nextBuild[number,url]"

    logger.debug(
        "making request to get the the id of the first st build of the commit from the most recent PR",
        url=first_jenkins_build_of_current_pull_request_apis_url,
    )
    first_jenkins_build_of_current_pull_request = make_request(
        APIS.DIRECT_JENKINS, first_jenkins_build_of_current_pull_request_apis_url
    )

    if not first_jenkins_build_of_current_pull_request["success"]:
        raise FiveHundredError(response=first_jenkins_build_of_current_pull_request)

    green_build = False

    try:
        build_result = first_jenkins_build_of_current_pull_request["data"]["result"]
        build_number = first_jenkins_build_of_current_pull_request["data"]["number"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    if build_result != "SUCCESS":
        while green_build != True:
            jenkins_build_of_current_pull_request_apis_retry_url = f"{global_variables['JENKINS_ST_JOB_NAME']}/{str(int(build_number) + 1)}/api/json?tree=displayName,result,number,id,fullDisplayName,duration,timestamp,url,inProgress,nextBuild[number,url]"

            first_jenkins_build_of_current_pull_request = make_request(
                APIS.JENKINS, jenkins_build_of_current_pull_request_apis_retry_url
            )

            if not first_jenkins_build_of_current_pull_request["success"]:
                raise FiveHundredError(
                    response=first_jenkins_build_of_current_pull_request
                )

            try:
                build_result = first_jenkins_build_of_current_pull_request["data"][
                    "result"
                ]
                build_number = first_jenkins_build_of_current_pull_request["data"][
                    "number"
                ]
            except KeyError as err:
                raise FiveHundredError(
                    message=f"Key {str(err)} cannot be found in the dict"
                )

            green_build = build_result == "SUCCESS"

    logger.debug(
        "successful request to jenkins to get the the id of the first st build of the commit from the most recent PR",
        url=first_jenkins_build_of_current_pull_request_apis_url,
        response=first_jenkins_build_of_current_pull_request,
    )
    return (
        first_jenkins_build_of_current_pull_request_apis_url,
        first_jenkins_build_of_current_pull_request,
    )


def extract_first_jenkins_build_of_current_pull_request(
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


def get_first_jenkins_build_of_current_pull_request(
    global_variables,
    first_jenkins_build_of_current_pull_request_url,
):
    (
        first_jenkins_build_of_current_pull_request_apis_url,
        first_jenkins_build_of_current_pull_request,
    ) = fetch_first_jenkins_build_of_current_pull_request(
        global_variables, first_jenkins_build_of_current_pull_request_url
    )

    try:
        (
            first_jenkins_build_of_current_pull_request_id,
            first_jenkins_build_of_current_pull_request_timestamp,
        ) = extract_first_jenkins_build_of_current_pull_request(
            first_jenkins_build_of_current_pull_request
        )
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            message=f"Unexpected data from {first_jenkins_build_of_current_pull_request_apis_url} in {global_variables['BITBUCKET_REPO_SLUG']} staging job. Visit {first_jenkins_build_of_current_pull_request_apis_url}"
        )

    if first_jenkins_build_of_current_pull_request_id == 1:
        logger.info("line 320")
        raise JenkinsHistoryLimit()

    return (
        first_jenkins_build_of_current_pull_request_id,
        first_jenkins_build_of_current_pull_request_timestamp,
    )


def get_at_jenkins_build_of_current_pull_request(
    global_variables,
    first_jenkins_build_of_current_pull_request_id,
):
    first_jenkins_at_build_of_current_pull_request_path = f"{global_variables['JENKINS_AT_JOB_NAME']}/api/xml?tree=allBuilds[number,url,result,actions[causes[upstreamUrl,upstreamBuild]]]&xpath=/workflowJob/allBuild/action/cause[upstreamBuild={first_jenkins_build_of_current_pull_request_id}%20and%20contains(upstreamUrl,%20%27main%27)%20and%20contains(upstreamUrl,%20%27Beehive%2520Improvement%2520Program%27)]/../.."

    logger.debug(
        "making request to get the the id of the first at build of the commit from the most recent PR",
        path=first_jenkins_at_build_of_current_pull_request_path,
    )
    first_jenkins_at_build_of_current_pull_request = make_request(
        APIS.JENKINS, first_jenkins_at_build_of_current_pull_request_path
    )

    if not first_jenkins_at_build_of_current_pull_request["success"]:
        if first_jenkins_at_build_of_current_pull_request["statusCode"] == 404:
            logger.info(
                "line 334",
                extra={
                    "request-path-made": first_jenkins_at_build_of_current_pull_request_path
                },
            )
            raise JenkinsHistoryLimit()
        raise FiveHundredError(response=first_jenkins_at_build_of_current_pull_request)

    logger.debug(
        "successful request to jenkins to get the the id of the first at build of the commit from the most recent PR",
        path=first_jenkins_at_build_of_current_pull_request_path,
        response=first_jenkins_at_build_of_current_pull_request,
    )

    green_build = False

    try:
        build_result = first_jenkins_at_build_of_current_pull_request["data"][
            "allBuild"
        ]["result"]
        build_number = first_jenkins_at_build_of_current_pull_request["data"][
            "allBuild"
        ]["number"]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    if build_result != "SUCCESS":
        while green_build != True:
            jenkins_at_build_of_current_pull_request_path_retry_url = f"{global_variables['JENKINS_AT_JOB_NAME']}/api/xml?tree=allBuilds[number,url,result,actions[causes[upstreamUrl,upstreamBuild]]]&xpath=/workflowJob/allBuild[number={str(int(build_number) + 1)}]"

            first_jenkins_at_build_of_current_pull_request = make_request(
                APIS.JENKINS, jenkins_at_build_of_current_pull_request_path_retry_url
            )

            if not first_jenkins_at_build_of_current_pull_request["success"]:
                raise FiveHundredError(
                    response=first_jenkins_at_build_of_current_pull_request
                )

            try:
                build_result = first_jenkins_at_build_of_current_pull_request["data"][
                    "allBuild"
                ]["result"]
                build_number = first_jenkins_at_build_of_current_pull_request["data"][
                    "allBuild"
                ]["number"]
            except KeyError as err:
                raise FiveHundredError(
                    message=f"Key {str(err)} cannot be found in the dict"
                )

            green_build = build_result == "SUCCESS"

    try:
        first_jenkins_at_build_of_current_pull_request_id = (
            first_jenkins_at_build_of_current_pull_request["data"]["allBuild"]["number"]
        )
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            f"Unexpected data from {first_jenkins_at_build_of_current_pull_request_path} in {global_variables['BITBUCKET_REPO_SLUG']} acceptance job. Visit {first_jenkins_at_build_of_current_pull_request_path}"
        )

    if first_jenkins_at_build_of_current_pull_request_id == 1:
        raise JenkinsHistoryLimit()

    return first_jenkins_at_build_of_current_pull_request_id


def get_pr_jenkins_build_of_current_pull_request(
    global_variables,
    first_jenkins_at_build_of_current_pull_request_id,
):
    first_jenkins_pr_build_of_current_pull_request_path = f"{global_variables['JENKINS_PR_JOB_NAME']}/api/xml?tree=allBuilds[duration,timestamp,number,url,actions[causes[upstreamUrl,upstreamBuild]]]&xpath=/workflowJob/allBuild/action/cause[upstreamBuild%20=%20%27{first_jenkins_at_build_of_current_pull_request_id}%27]/../.."

    logger.debug(
        "making request to get the the id of the first prod build of the commit from the most recent PR",
        path=first_jenkins_pr_build_of_current_pull_request_path,
    )
    first_jenkins_pr_build_of_current_pull_request = make_request(
        APIS.JENKINS, first_jenkins_pr_build_of_current_pull_request_path
    )

    if not first_jenkins_pr_build_of_current_pull_request["success"]:
        if first_jenkins_pr_build_of_current_pull_request["statusCode"] == 404:
            raise JenkinsHistoryLimit()
        raise FiveHundredError(response=first_jenkins_pr_build_of_current_pull_request)

    logger.debug(
        "successful request to jenkins to",
        path=first_jenkins_pr_build_of_current_pull_request_path,
        response=first_jenkins_pr_build_of_current_pull_request,
    )

    try:
        first_jenkins_pr_build_of_current_pull_request_duration_seconds = int(
            first_jenkins_pr_build_of_current_pull_request["data"]["allBuild"][
                "duration"
            ]
        )
        first_jenkins_pr_build_of_current_pull_request_start_timestamp = int(
            first_jenkins_pr_build_of_current_pull_request["data"]["allBuild"][
                "timestamp"
            ]
        )
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")
    except IndexError as err:
        raise FiveHundredError(
            f"Unexpected data from {first_jenkins_pr_build_of_current_pull_request_path} in {global_variables['BITBUCKET_REPO_SLUG']} production job. Visit {first_jenkins_pr_build_of_current_pull_request_path}"
        )

    return (
        first_jenkins_pr_build_of_current_pull_request_duration_seconds,
        first_jenkins_pr_build_of_current_pull_request_start_timestamp,
    )
