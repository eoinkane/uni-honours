from __future__ import annotations
import os
from typing_extensions import TypedDict, NotRequired
from aws_lambda_powertools import Logger
from .shared import (
    extract_parent_commits,
    fetch_parent_commit_statuses,
    get_last_build_of_parent_commit,
    get_first_jenkins_build_of_current_pull_request,
    get_at_jenkins_build_of_current_pull_request,
    get_pr_jenkins_build_of_current_pull_request,
    JenkinsHistoryLimit
)
from ..helpers.datetime import jenkins_build_datetime

logger = Logger(child=True)


def calculate_lead_time_for_changes(pull_request) -> int:
    (
        parent_commit_hash,
        parent_commit_hash_url,
        statuses_of_parent_commit_url,
    ) = extract_parent_commits(pull_request)

    last_build_of_parent_commit_display_url = fetch_parent_commit_statuses(
        parent_commit_hash, parent_commit_hash_url, statuses_of_parent_commit_url
    )

    if "master" in last_build_of_parent_commit_display_url:
        raise JenkinsHistoryLimit()

    first_jenkins_build_of_current_pull_request_url = get_last_build_of_parent_commit(
        last_build_of_parent_commit_display_url
    )

    (
        first_jenkins_build_of_current_pull_request_id,
        first_jenkins_build_of_current_pull_request_timestamp,
    ) = get_first_jenkins_build_of_current_pull_request(
        first_jenkins_build_of_current_pull_request_url
    )

    first_jenkins_build_of_current_pull_request_datetime = jenkins_build_datetime(
        {"timestamp": first_jenkins_build_of_current_pull_request_timestamp}
    )

    first_jenkins_at_build_of_current_pull_request_id = (
        get_at_jenkins_build_of_current_pull_request(
            first_jenkins_build_of_current_pull_request_id
        )
    )

    (
        first_jenkins_pr_build_of_current_pull_request_duration_seconds,
        first_jenkins_pr_build_of_current_pull_request_start_timestamp,
    ) = get_pr_jenkins_build_of_current_pull_request(
        first_jenkins_at_build_of_current_pull_request_id
    )

    # eighth section

    first_jenkins_pr_build_of_current_pull_request_finish_timestamp = (
        first_jenkins_pr_build_of_current_pull_request_start_timestamp
        + first_jenkins_pr_build_of_current_pull_request_duration_seconds
    )

    first_jenkins_pr_build_of_current_pull_request_finish_datetime = jenkins_build_datetime(
        {"timestamp": first_jenkins_pr_build_of_current_pull_request_finish_timestamp}
    )

    duration = (
        first_jenkins_pr_build_of_current_pull_request_finish_datetime
        - first_jenkins_build_of_current_pull_request_datetime
    )

    return duration.total_seconds()
