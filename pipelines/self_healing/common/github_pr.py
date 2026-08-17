from __future__ import annotations

import base64
import os

import requests

from pipelines.self_healing.common.llm_diagnostician import Diagnosis

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_PR_BASE_BRANCH = os.environ.get("GITHUB_PR_BASE_BRANCH", "main")

REQUEST_TIMEOUT_SECONDS = 10


def _validate_configuration(repo: str) -> None:
    if not repo or "/" not in repo:
        raise ValueError("GITHUB_REPO must use the 'owner/repository' format")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def _get_base_sha(repo: str, base_branch: str) -> str:
    resp = requests.get(
        f"{GITHUB_API_BASE}/repos/{repo}/git/ref/heads/{base_branch}",
        headers=_headers(),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()["object"]["sha"]


def create_branch(repo: str, branch_name: str, base_branch: str = GITHUB_PR_BASE_BRANCH) -> None:
    base_sha = _get_base_sha(repo, base_branch)
    resp = requests.post(
        f"{GITHUB_API_BASE}/repos/{repo}/git/refs",
        headers=_headers(),
        json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()


def _get_file_sha(repo: str, path: str, ref: str) -> str | None:
    resp = requests.get(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
        headers=_headers(),
        params={"ref": ref},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["sha"]


def commit_file(repo: str, branch: str, target_file: str, content: str, message: str) -> None:
    existing_sha = _get_file_sha(repo, target_file, branch)
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    resp = requests.put(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{target_file}",
        headers=_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()


def open_pull_request(
    repo: str, branch: str, title: str, body: str, base_branch: str = GITHUB_PR_BASE_BRANCH
) -> str:
    resp = requests.post(
        f"{GITHUB_API_BASE}/repos/{repo}/pulls",
        headers=_headers(),
        json={"title": title, "head": branch, "base": base_branch, "body": body},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()["html_url"]


def propose_fix_as_pr(diagnosis: Diagnosis, event_id: str, log_link: str, repo: str = GITHUB_REPO) -> str:
    _validate_configuration(repo)
    branch_name = f"self-healing/{event_id[:8]}"
    title = f"self-healing: {diagnosis.root_cause[:72]}"
    body = (
        f"**Causa raiz:** {diagnosis.root_cause}\n\n"
        f"**Tipo de correção:** {diagnosis.fix_type}\n\n"
        f"**Explicação:** {diagnosis.explanation}\n\n"
        f"**Log da falha original:** {log_link}\n\n"
        "_Aberto automaticamente pelo agente de self-healing — revisão humana obrigatória antes do merge._"
    )

    create_branch(repo, branch_name)
    commit_file(
        repo=repo,
        branch=branch_name,
        target_file=diagnosis.target_file,
        content=diagnosis.diff,
        message=title,
    )
    return open_pull_request(repo=repo, branch=branch_name, title=title, body=body)
