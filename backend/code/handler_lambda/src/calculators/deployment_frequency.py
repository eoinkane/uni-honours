from __future__ import annotations
from typing_extensions import TypedDict, NotRequired

from ..helpers.datetime import jenkins_build_datetime


class DeploymentFrequencyData(TypedDict):
    numberOfDeployments: str
    latestBuildDatetime: str
    firstBuildDatetime: str
    daysBetweenLatestAndFirstBuild: int


class DeploymentFrequencyResult(TypedDict):
    success: bool
    message: NotRequired[str | None]
    data: NotRequired[DeploymentFrequencyData | None]


def calculate_deployment_frequency(
    jenkins_api_response: dict,
) -> DeploymentFrequencyResult:
    return_value: DeploymentFrequencyResult
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
            for build in jenkins_api_response["builds"]
            if build["result"] == "SUCCESS"
        ]
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
        if time_delta_between_latest_and_first_build.days > 0:
            days_between_latest_and_first_build = (
                time_delta_between_latest_and_first_build.days
            )
        else:
            return_value = {
                "success": False,
                "message": "unexpected duration between latest and first build of the job in jenkins",
            }
            return return_value
        return_value = {
            "success": True,
            "data": {
                "numberOfDeployments": number_of_deployments,
                "latestBuildDatetime": latest_build_datetime.isoformat(),
                "firstBuildDatetime": first_build_datetime.isoformat(),
                "daysBetweenLatestAndFirstBuild": days_between_latest_and_first_build,
            },
            "message": "deployment frequency successfully calculated",
        }
        return return_value
    except KeyError as err:
        return_value = {
            "success": False,
            "message": f"Key {str(err)} cannot be found in the dict",
        }
        return return_value
