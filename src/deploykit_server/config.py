import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = ""
    app_path: str = ""
    max_deployments: int = 500


class ProjectPath:
    def __init__(self, app_path: str, project_name: str):
        self.app_path = os.path.abspath(app_path)
        self.project_name = project_name

        # {root}/{project_name}
        self.project_path = os.path.join(self.app_path, project_name)

        # {root}/{project_name}/current -> ?
        self.current_symlink = os.path.join(self.project_path, "current")

        # {root}/{project_name}/deployments/
        self.deployments_path = os.path.join(self.project_path, "deployments")

        # {root}/{project_name}/commits/
        self.commits_path = os.path.join(self.project_path, "commits")

    def deployment(self, deployment_id: str):
        # {root}/{project_name}/deployments/{deployment_id}/
        return os.path.join(self.deployments_path, deployment_id)
    
    def commit_symlink(self, commit_id: str):
        # {root}/{project_name}/commits/{commit_id}
        return os.path.join(self.commits_path, commit_id)


if not os.environ.get("API_KEY") or os.environ.get("API_KEY").strip() == "":
    raise ValueError("API_KEY is not set or empty")
