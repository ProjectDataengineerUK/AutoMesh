from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipelines.self_healing.common.github_pr import (
    commit_file,
    create_branch,
    open_pull_request,
    propose_fix_as_pr,
)
from pipelines.self_healing.common.llm_diagnostician import Diagnosis


def test_propose_fix_rejects_invalid_repository() -> None:
    diagnosis = Diagnosis("cause", "code", "pipelines/processing/job.py", "content", "explanation")

    with pytest.raises(ValueError, match="owner/repository"):
        propose_fix_as_pr(diagnosis, "event-1", "log", repo="")


@patch("pipelines.self_healing.common.github_pr.requests")
def test_create_branch_uses_base_branch_sha(mock_requests) -> None:
    ref_response = MagicMock()
    ref_response.json.return_value = {"object": {"sha": "abc123"}}
    mock_requests.get.return_value = ref_response

    create_branch("owner/repo", "self-healing/xyz", base_branch="main")

    mock_requests.get.assert_called_once()
    post_kwargs = mock_requests.post.call_args.kwargs
    assert post_kwargs["json"]["ref"] == "refs/heads/self-healing/xyz"
    assert post_kwargs["json"]["sha"] == "abc123"


@patch("pipelines.self_healing.common.github_pr.requests")
def test_commit_file_creates_new_file_without_sha(mock_requests) -> None:
    mock_requests.get.return_value = MagicMock(status_code=404)

    commit_file("owner/repo", "branch", "pipelines/processing/x.py", "print(1)", "fix")

    put_kwargs = mock_requests.put.call_args.kwargs
    assert "sha" not in put_kwargs["json"]


@patch("pipelines.self_healing.common.github_pr.requests")
def test_commit_file_updates_existing_file_with_sha(mock_requests) -> None:
    existing_response = MagicMock(status_code=200)
    existing_response.json.return_value = {"sha": "existing-sha"}
    mock_requests.get.return_value = existing_response

    commit_file("owner/repo", "branch", "pipelines/processing/x.py", "print(1)", "fix")

    put_kwargs = mock_requests.put.call_args.kwargs
    assert put_kwargs["json"]["sha"] == "existing-sha"


@patch("pipelines.self_healing.common.github_pr.requests")
def test_open_pull_request_returns_html_url(mock_requests) -> None:
    pr_response = MagicMock()
    pr_response.json.return_value = {"html_url": "https://github.com/owner/repo/pull/1"}
    mock_requests.post.return_value = pr_response

    url = open_pull_request("owner/repo", "branch", "title", "body")

    assert url == "https://github.com/owner/repo/pull/1"


@patch("pipelines.self_healing.common.github_pr.open_pull_request")
@patch("pipelines.self_healing.common.github_pr.commit_file")
@patch("pipelines.self_healing.common.github_pr.create_branch")
def test_propose_fix_as_pr_orchestrates_full_flow(mock_create_branch, mock_commit_file, mock_open_pr) -> None:
    mock_open_pr.return_value = "https://github.com/owner/repo/pull/2"
    diagnosis = Diagnosis(
        root_cause="causa",
        fix_type="contract",
        target_file="pipelines/ingestion/contracts/b3_quotes.contract.yaml",
        diff="schema: {}",
        explanation="explicação",
    )

    url = propose_fix_as_pr(diagnosis, event_id="abcdef1234", log_link="link", repo="owner/repo")

    assert url == "https://github.com/owner/repo/pull/2"
    mock_create_branch.assert_called_once()
    mock_commit_file.assert_called_once()
    mock_open_pr.assert_called_once()
