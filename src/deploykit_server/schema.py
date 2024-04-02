import uuid
from datetime import datetime, timezone


ProjectName = {
    'pattern': "^[A-Za-z0-9_][A-Za-z0-9_-]{0,61}[A-Za-z0-9_]$",
    'max_length': 63,
}

CommitHash = {
    'min_length': 40,
    'max_length': 40,
    'pattern': "^[a-f0-9]{40}$",
}

DeploymentId = {
    'min_length': 33,
    'max_length': 33,
    'pattern': "^[0-9]{8}-[0-9]{6}-[0-9a-z]{4}-[0-9a-z]{12}$",
}


def generate_deployment_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + str(uuid.uuid4())[18:]
