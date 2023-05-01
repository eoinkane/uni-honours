from datetime import datetime, timezone

def jenkins_build_datetime(jenkins_build) -> datetime:
    return datetime.fromtimestamp(jenkins_build["timestamp"] / 1000.0, timezone.utc)
