from aws_lambda_powertools import Logger
from .shared import (
    extract_parent_commits,
    fetch_parent_commit_statuses,
    get_last_build_of_parent_commit,
    get_first_jenkins_build_of_current_pull_request,
    get_at_jenkins_build_of_current_pull_request,
    get_pr_jenkins_build_of_current_pull_request,
)
from ..exceptions import FiveHundredError, JenkinsHistoryLimit

logger = Logger(child=True)


def filter_only_hotfix_pull_requests(pull_requests):
    max_pull_requests_count = len(pull_requests) + 1
    filtered_pull_request_indexes = []

    for index, pull_request in enumerate(pull_requests):
        try:
            if (
                index < max_pull_requests_count
                and "hotfix" in pull_request["source"]["branch"]["name"]
            ):
                filtered_pull_request_indexes.append(index)
        except KeyError as err:
            raise FiveHundredError(
                message=f"Key {str(err)} cannot be found in the dict"
            )

    return filtered_pull_request_indexes


def filter_out_hotfix_pull_requests(pull_requests):
    filtered_pull_request_indexes = filter_only_hotfix_pull_requests(pull_requests)

    filtered_pull_request_with_non_hotfixes = []
    for i, pull_request_index in enumerate(filtered_pull_request_indexes):
        higher_pull_request_index = pull_request_index + 1
        filtered_pull_request_with_non_hotfixes.append(
            pull_requests[pull_request_index]
        )
        if i < (len(filtered_pull_request_indexes) - 1):
            if filtered_pull_request_indexes[i + 1] != higher_pull_request_index:
                filtered_pull_request_with_non_hotfixes.append(
                    pull_requests[higher_pull_request_index]
                )
        else:
            if pull_request_index < len(pull_requests):
                filtered_pull_request_with_non_hotfixes.append(
                    pull_requests[higher_pull_request_index]
                )

    return filtered_pull_request_with_non_hotfixes


def get_timestamp_of_pr_build_of_pull_request(global_variables, pull_request):
    (
        parent_commit_hash,
        parent_commit_hash_url,
        statuses_of_parent_commit_url,
    ) = extract_parent_commits(global_variables, pull_request)

    last_build_of_parent_commit_display_url = fetch_parent_commit_statuses(
        global_variables,
        parent_commit_hash,
        parent_commit_hash_url,
        statuses_of_parent_commit_url,
    )

    if "master" in last_build_of_parent_commit_display_url:
        raise JenkinsHistoryLimit()

    first_jenkins_build_of_current_pull_request_url = get_last_build_of_parent_commit(
        global_variables, last_build_of_parent_commit_display_url
    )

    (
        first_jenkins_build_of_current_pull_request_id,
        _,
    ) = get_first_jenkins_build_of_current_pull_request(
        global_variables, first_jenkins_build_of_current_pull_request_url
    )

    first_jenkins_at_build_of_current_pull_request_id = (
        get_at_jenkins_build_of_current_pull_request(
            global_variables, first_jenkins_build_of_current_pull_request_id
        )
    )

    (
        first_jenkins_pr_build_of_current_pull_request_duration_seconds,
        first_jenkins_pr_build_of_current_pull_request_start_timestamp,
    ) = get_pr_jenkins_build_of_current_pull_request(
        global_variables, first_jenkins_at_build_of_current_pull_request_id
    )

    first_jenkins_pr_build_of_current_pull_request_finish_timestamp = (
        first_jenkins_pr_build_of_current_pull_request_start_timestamp
        + first_jenkins_pr_build_of_current_pull_request_duration_seconds
    )

    return first_jenkins_pr_build_of_current_pull_request_finish_timestamp
