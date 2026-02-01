"""Wishlist management router."""

from uuid import UUID

from common.models import (
    AuthenticatedUser,
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistItemUpdate,
)
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from services.groups_service import BadRequestError, ForbiddenError, NotFoundError
from services.wishlist_service import WishlistService

router = APIRouter()


def get_wishlist_service() -> WishlistService:
    """Dependency to get wishlist service instance."""
    return WishlistService()


@router.get("", response_model=dict[str, list[WishlistItemResponse]])
async def get_wishlist(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Get all wishlist items for the authenticated user."""
    user_id = str(current_user.sub)
    items = service.get_user_wishlist(user_id)
    return {"items": items}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WishlistItemResponse)
async def create_wishlist_item(
    item_data: WishlistItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Create a new wishlist item."""
    user_id = str(current_user.sub)

    try:
        return service.create_wishlist_item(
            user_id=user_id,
            name=item_data.name,
            description=item_data.description,
            url=str(item_data.url) if item_data.url else None,
            price=item_data.price,
            photo_url=str(item_data.photo_url) if item_data.photo_url else None,
            rank=item_data.rank,
            group_ids=item_data.group_ids,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/{item_id}", response_model=WishlistItemResponse)
async def get_wishlist_item(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Get a single wishlist item."""
    user_id = str(current_user.sub)

    try:
        return service.get_wishlist_item(user_id, str(item_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.put("/{item_id}", response_model=WishlistItemResponse)
async def update_wishlist_item(
    item_id: UUID,
    update_data: WishlistItemUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Update a wishlist item (owner only)."""
    user_id = str(current_user.sub)

    try:
        return service.update_wishlist_item(
            user_id=user_id,
            item_id=str(item_id),
            name=update_data.name,
            description=update_data.description,
            url=str(update_data.url) if update_data.url else None,
            price=update_data.price,
            photo_url=str(update_data.photo_url) if update_data.photo_url else None,
            rank=update_data.rank,
            group_ids=update_data.group_ids,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/reorder")
async def reorder_wishlist_items(
    reorder_data: dict[str, list[dict]],
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Reorder wishlist items by updating rank values."""
    user_id = str(current_user.sub)
    items = reorder_data.get("items", [])

    try:
        service.reorder_items(user_id, items)
        return {"success": True}
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: WishlistService = Depends(get_wishlist_service),
):
    """Delete a wishlist item (owner only)."""
    user_id = str(current_user.sub)

    try:
        service.delete_wishlist_item(user_id, str(item_id))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
