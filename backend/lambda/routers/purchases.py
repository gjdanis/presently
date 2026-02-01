"""Purchase management router."""

from uuid import UUID

from common.models import AuthenticatedUser, PurchaseCreate, PurchaseResponse
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from services.groups_service import BadRequestError, ForbiddenError, NotFoundError
from services.purchases_service import ConflictError, PurchasesService

router = APIRouter()


def get_purchases_service() -> PurchasesService:
    """Dependency to get purchases service instance."""
    return PurchasesService()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PurchaseResponse)
async def claim_item(
    purchase_data: PurchaseCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: PurchasesService = Depends(get_purchases_service),
):
    """Claim (purchase) a wishlist item."""
    user_id = str(current_user.sub)
    item_id = str(purchase_data.item_id)
    group_id = str(purchase_data.group_id)

    try:
        return service.claim_item(user_id, item_id, group_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete("/{item_id}/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unclaim_item(
    item_id: UUID,
    group_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: PurchasesService = Depends(get_purchases_service),
):
    """Unclaim (un-purchase) a wishlist item."""
    user_id = str(current_user.sub)

    try:
        service.unclaim_item(user_id, str(item_id), str(group_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
