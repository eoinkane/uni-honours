from datetime import datetime, timezone


def jenkins_build_datetime(jenkins_build) -> datetime:
    return datetime.fromtimestamp(jenkins_build["timestamp"] / 1000.0, timezone.utc)


def timedelta_to_string(duration):
    return str(duration).split('.')[0].replace(':', ' hr(s), ', 1).replace(':', ' min(s), ', 1) + ' sec(s)'
