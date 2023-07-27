from __future__ import annotations
from typing_extensions import TypedDict, NotRequired
from datetime import timedelta

from ..helpers.datetime import jenkins_build_datetime, timedelta_to_string
from .shared import FiveHundredError


class DeploymentFrequency(TypedDict):
    numberOfDeployments: str
    latestBuildDatetime: str
    firstBuildDatetime: str
    daysBetweenLatestAndFirstBuild: int


def calculate_deployment_frequency(
    jenkins_api_response: dict,
) -> DeploymentFrequency:
    try:
        # this commented out section is for multibranch pipelines
        # main_jenkins_job_list = [
        #     job for job in jenkins_api_response["jobs"] if job["name"] == "main"
        # ]
        # if len(main_jenkins_job_list) > 1:
        #     return_value = {
        #         "success": False,
        #         "message": "unexpected number of sub jobs with name main for job in jenkins",
        #     }
        #     return return_value
        # main_jenkins_job = main_jenkins_job_list[0]
        successful_builds_from_jenkins_job = [
            build
            for build in jenkins_api_response["allBuilds"]
            if build["result"] == "SUCCESS"
        ]
    except KeyError as err:
        raise FiveHundredError(message=f"Key {str(err)} cannot be found in the dict")

    number_of_deployments = len(successful_builds_from_jenkins_job)
    latest_build_datetime = jenkins_build_datetime(
        successful_builds_from_jenkins_job[0]
    )
    first_build_datetime = jenkins_build_datetime(
        successful_builds_from_jenkins_job[-1]
    )

    time_delta_between_latest_and_first_build = (
        latest_build_datetime - first_build_datetime
    )

    time_between_builds_str = timedelta_to_string(
        timedelta(seconds=time_delta_between_latest_and_first_build.total_seconds())
    )

    return {
        "numberOfDeployments": number_of_deployments,
        "latestBuildDatetime": latest_build_datetime.isoformat(),
        "firstBuildDatetime": first_build_datetime.isoformat(),
        "timeBetweenLatestAndFirstBuild": time_between_builds_str,
    }
