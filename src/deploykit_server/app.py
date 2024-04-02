import os
import shutil
from typing import Annotated
from fastapi import FastAPI, Depends, Request, Path, Query, UploadFile
from fastapi.responses import JSONResponse
from functools import lru_cache

from deploykit_server import schema
from deploykit_server import archive
from deploykit_server.config import Settings, ProjectPath


app = FastAPI()


@lru_cache
def get_settings():
    return Settings()


@app.exception_handler(500)
async def internal_exception_handler(_request: Request, _e: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.middleware("http")
async def authorize_api_key(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(status_code=401,
                            content={"detail": "Unauthorized: Missing 'Authorization' header"})
    if not authorization.startswith("APIKey "):
        return JSONResponse(status_code=401,
                            content={"detail": "Unauthorized: Malformed 'Authorization' header, should start with 'APIKey '"})
    api_key = authorization[len("APIKey "):].strip()
    if api_key != get_settings().api_key:
        return JSONResponse(status_code=401,
                            content={"detail": "Unauthorized: Invalid API key"})
    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    return {"healthy": True}


@app.get("/projects/{project_name}/deployments")
async def list_deployments(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    project_path = ProjectPath(settings.app_path, project_name)
    try:
        deployments = os.listdir(project_path.deployments_path)
        deployments = [x for x in deployments if (not x.startswith(".")) and len(x) == schema.DeploymentId['min_length']]
        deployments = sorted(deployments, reverse=True)
        deployments = [{
            "deployment_id": x,
            "created_at": int(os.path.getctime(project_path.deployment(x))),
        } for x in deployments]
    except FileNotFoundError:
        deployments = []
    finally:
        return {"name": project_name, "deployments": deployments[:settings.max_deployments]}


@app.post("/projects/{project_name}/deployments")
async def create_deployment(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
    upload: UploadFile,
    commit_hash: Annotated[str | None, Query(**schema.CommitHash)] = None,
):
    project_path = ProjectPath(settings.app_path, project_name)
    deployment_id = schema.generate_deployment_id()
    deployment_path = project_path.deployment(deployment_id)
    zstd_size, tar_size = archive.decompress(upload, deployment_path)

    if commit_hash:
        commit_symlink = project_path.commit_symlink(commit_hash)
        if os.path.exists(commit_symlink):
            os.unlink(commit_symlink)
        os.makedirs(project_path.commits_path, exist_ok=True)
        os.symlink(f"../deployments/{deployment_id}/", commit_symlink, target_is_directory=True)
    return {"name": project_name, "deployment_id": deployment_id, "commit_hash": commit_hash,
            "upload_size": zstd_size, "extracted_size": tar_size}


@app.get("/projects/{project_name}/commits")
async def list_commits(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    project_path = ProjectPath(settings.app_path, project_name)
    try:
        commits = os.listdir(project_path.commits_path)
        commits = [x for x in commits if (not x.startswith(".")) and len(x) == schema.CommitHash['min_length']]
        commits = sorted(commits, key=lambda x: os.path.getmtime(project_path.commit_symlink(x)), reverse=True)
        commits = [{
            "commit_hash": x,
            "deployment_id": os.path.basename(os.readlink(project_path.commit_symlink(x))),
            "created_at": int(os.path.getctime(project_path.commit_symlink(x))),
        } for x in commits]
    except FileNotFoundError:
        commits = []
    finally:
        return {"name": project_name, "commits": commits[:settings.max_deployments]}   


@app.patch("/projects/{project_name}/current")
async def switch_current(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
    deployment_id: Annotated[str, Query(**schema.DeploymentId)],
):
    project_path = ProjectPath(settings.app_path, project_name)
    deployment_path = project_path.deployment(deployment_id)
    if not os.path.exists(deployment_path):
        return JSONResponse(status_code=404, content={"detail": "Deployment not found"})
    try:
        os.unlink(project_path.current_symlink)
    except FileNotFoundError:
        pass
    os.symlink(f"deployments/{deployment_id}/", project_path.current_symlink, target_is_directory=True)
    return {"name": project_name, "deployment_id": deployment_id}


@app.delete("/projects/{project_name}/deployments/{deployment_id}")
async def delete_deployment(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
    deployment_id: Annotated[str, Path(**schema.DeploymentId)],
):
    project_path = ProjectPath(settings.app_path, project_name)
    deployment_path = project_path.deployment(deployment_id)
    try:
        shutil.rmtree(deployment_path, ignore_errors=True)
        return {"name": project_name, "deployment_id": deployment_id}
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Deployment not found"})


@app.delete("/projects/{project_name}/commits/{commit_hash}")
async def delete_commit(
    project_name: Annotated[str, Path(**schema.ProjectName)],
    settings: Annotated[Settings, Depends(get_settings)],
    commit_hash: Annotated[str, Path(**schema.CommitHash)],
):
    project_path = ProjectPath(settings.app_path, project_name)
    commit_symlink = project_path.commit_symlink(commit_hash)
    deployment_path = os.readlink(commit_symlink)
    try:
        if os.path.exists(deployment_path):
            shutil.rmtree(deployment_path, ignore_errors=True)
        os.unlink(commit_symlink)
        return {"name": project_name, "commit_hash": commit_hash}
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Commit not found"})
