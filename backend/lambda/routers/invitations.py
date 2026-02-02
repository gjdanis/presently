"""Group invitations router."""

from common.models import (
    AuthenticatedUser,
    InvitationAcceptResponse,
    InvitationResponse,
)
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from services.groups_service import BadRequestError, ForbiddenError, NotFoundError
from services.invitations_service import GoneError, InvitationsService

router = APIRouter()


def get_invitations_service() -> InvitationsService:
    """Dependency to get invitations service instance."""
    return InvitationsService()


@router.get("/{token}", response_model=InvitationResponse)
async def get_invitation(
    token: str, service: InvitationsService = Depends(get_invitations_service)
):
    """Get invitation details (public endpoint)."""
    try:
        return service.get_invitation(token)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except GoneError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e)) from e


@router.post("/{token}/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    token: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: InvitationsService = Depends(get_invitations_service),
):
    """Accept a group invitation."""
    user_id = str(current_user.sub)

    try:
        return service.accept_invitation(user_id, token)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except GoneError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete("/{token}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    token: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: InvitationsService = Depends(get_invitations_service),
):
    """Revoke an invitation (admin only)."""
    user_id = str(current_user.sub)

    try:
        service.revoke_invitation(user_id, token)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
