"""Feedback router — creates GitHub issues from in-app feedback submissions."""

import os

import httpx
from common.models import AuthenticatedUser
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class FeedbackRequest(BaseModel):
    title: str | None = None
    body: str


@router.post("")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")

    if not github_token or not github_repo:
        raise HTTPException(status_code=503, detail="Feedback is not configured")

    issue_title = request.title.strip() if request.title and request.title.strip() else f"Feedback from {current_user.name}"
    issue_title = f"[Feedback] {issue_title}"

    issue_body = f"**From:** {current_user.name} ({current_user.email})\n\n{request.body}\n\n---\n*Submitted via Presently*"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{github_repo}/issues",
                json={
                    "title": issue_title,
                    "body": issue_body,
                    "labels": ["feedback"],
                },
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            return {"issue_url": response.json()["html_url"]}
    except httpx.HTTPError as err:
        raise HTTPException(status_code=502, detail="Failed to create feedback issue") from err
