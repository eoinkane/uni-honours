import os
from .exceptions import FiveHundredError, FourTwoTwoError


JENKINS_ST_JOB_NAMES = [""] + os.getenv("JENKINS_ST_JOB_NAMES", "").split(",")
JENKINS_AT_JOB_NAMES = [""] + os.getenv("JENKINS_AT_JOB_NAMES", "").split(",")
JENKINS_PR_JOB_NAMES = [""] + os.getenv("JENKINS_PR_JOB_NAMES", "").split(",")
JENKINS_JOB_NAMES = [""] + os.getenv("JENKINS_JOB_NAMES", "").split(",")
BITBUCKET_REPO_SLUGS = [""] + os.getenv("BITBUCKET_REPO_SLUGS", "").split(",")

MIN_PROJECT_ID = 1
MAX_PROJECT_ID = 0

JENKINS_ST_JOB_NAME = ""
JENKINS_AT_JOB_NAME = ""
JENKINS_PR_JOB_NAME = ""
JENKINS_JOB_NAME = ""
BITBUCKET_REPO_SLUG = ""

global_variable_keys = [
    "JENKINS_ST_JOB_NAME",
    "JENKINS_AT_JOB_NAME",
    "JENKINS_PR_JOB_NAME",
    "JENKINS_JOB_NAME",
    "BITBUCKET_REPO_SLUG",
]


def validate_job_names():
    job_names = [
        len(JENKINS_ST_JOB_NAMES),
        len(JENKINS_AT_JOB_NAMES),
        len(JENKINS_PR_JOB_NAMES),
        len(JENKINS_JOB_NAMES),
        len(BITBUCKET_REPO_SLUGS),
    ]
    if job_names[:-1] != job_names[1:]:
        print(job_names)
        raise FiveHundredError(
            message="The job name env vars do not match. Environment variables need fixed before requests can be accepted."
        )
    elif len(JENKINS_JOB_NAMES) == 2 and JENKINS_JOB_NAMES[1] == "":
        raise FiveHundredError(
            message="Invalid job name env vars. Values are empty. Environment variables need fixed before requests can be accepted"
        )
    global MAX_PROJECT_ID
    MAX_PROJECT_ID = len(JENKINS_JOB_NAMES) - 1


def validate_project_id_param(request_id):
    validate_job_names()
    if request_id < MIN_PROJECT_ID or request_id > MAX_PROJECT_ID:
        raise FourTwoTwoError(f"Out of Bounds Request ID: {str(request_id)}")
    global_variables = {
        "JENKINS_ST_JOB_NAME": JENKINS_ST_JOB_NAMES[request_id],
        "JENKINS_AT_JOB_NAME": JENKINS_AT_JOB_NAMES[request_id],
        "JENKINS_PR_JOB_NAME": JENKINS_PR_JOB_NAMES[request_id],
        "JENKINS_JOB_NAME": JENKINS_JOB_NAMES[request_id],
        "BITBUCKET_REPO_SLUG": BITBUCKET_REPO_SLUGS[request_id],
    }
    if not (all(key in global_variables for key in global_variable_keys)) and all(
        global_variables[key] != "" for key in global_variable_keys
    ):
        raise FourTwoTwoError(
            f"global variables could not be created from the request ID: {str(request_id)}"
        )

    return global_variables
