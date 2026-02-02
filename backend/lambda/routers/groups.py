"""Groups management FastAPI router."""

from common.logger import setup_logger
from common.models import (
    AuthenticatedUser,
    GroupCreate,
    GroupDetailResponse,
    GroupResponse,
    GroupsListResponse,
    GroupUpdate,
    InvitationCreate,
    InvitationCreateResponse,
)
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Response, status
from services.groups_service import (
    BadRequestError,
    ForbiddenError,
    GroupsService,
    NotFoundError,
)

logger = setup_logger(__name__)

router = APIRouter()


def get_groups_service() -> GroupsService:
    """Dependency to get groups service instance."""
    return GroupsService()


@router.get("", response_model=GroupsListResponse)
async def get_groups(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> GroupsListResponse:
    """Get all groups for the authenticated user."""
    user_id = str(current_user.sub)
    groups = service.get_user_groups(user_id)
    return GroupsListResponse(groups=groups)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> GroupResponse:
    """Create a new group."""
    user_id = str(current_user.sub)

    try:
        return service.create_group(user_id, group_data.name, group_data.description)
    except BadRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group_detail(
    group_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> GroupDetailResponse:
    """Get detailed group information including members and wishlists."""
    user_id = str(current_user.sub)

    try:
        return service.get_group_detail(user_id, group_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{group_id}")
async def update_group(
    group_id: str,
    update_data: GroupUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> dict:
    """Update group details (admin only)."""
    user_id = str(current_user.sub)

    try:
        group = service.update_group(user_id, group_id, update_data.name, update_data.description)
        return {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> Response:
    """Delete a group (admin only)."""
    user_id = str(current_user.sub)

    try:
        service.delete_group(user_id, group_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{group_id}/members", response_model=InvitationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    group_id: str,
    invite_data: InvitationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> InvitationCreateResponse:
    """Create a group invitation link."""
    from services.invitations_service import InvitationsService

    service = InvitationsService()
    user_id = str(current_user.sub)

    try:
        return service.create_invitation(
            user_id=user_id,
            group_id=group_id,
            role=invite_data.role or "member",
            max_uses=invite_data.max_uses,
            expires_in_days=invite_data.expires_in_days,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/{group_id}/invitations/active")
async def get_active_invitations(
    group_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get list of active invitations for a group (admin only)."""
    from services.invitations_service import InvitationsService

    service = InvitationsService()
    user_id = str(current_user.sub)

    try:
        return service.get_active_invitations(user_id, group_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.delete("/{group_id}/members/{user_id_to_remove}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id_to_remove: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: GroupsService = Depends(get_groups_service),
) -> Response:
    """Remove a member from a group (admin only)."""
    user_id = str(current_user.sub)

    try:
        service.remove_member(user_id, group_id, user_id_to_remove)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
