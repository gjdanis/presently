"""Pydantic models for request/response validation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl


# ============================================================================
# Profile Models
# ============================================================================


class ProfileBase(BaseModel):
    """Base profile fields."""

    name: str = Field(..., min_length=1, max_length=255)


class ProfileCreate(ProfileBase):
    """Profile creation request."""

    email: EmailStr
    cognito_sub: UUID


class ProfileUpdate(BaseModel):
    """Profile update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ProfileResponse(ProfileBase):
    """Profile response."""

    id: UUID
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Group Models
# ============================================================================


class GroupBase(BaseModel):
    """Base group fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Group creation request."""

    pass


class GroupUpdate(BaseModel):
    """Group update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class GroupMemberResponse(BaseModel):
    """Group member details."""

    user_id: UUID
    name: str
    email: EmailStr
    role: str
    joined_at: datetime


class GroupResponse(GroupBase):
    """Group response with basic info."""

    id: UUID
    role: str  # Current user's role in this group
    member_count: int
    created_at: datetime
    updated_at: datetime


class GroupsListResponse(BaseModel):
    """Response for GET /groups endpoint."""

    groups: list[GroupResponse]


class GroupBasicInfo(GroupBase):
    """Basic group information for detail view."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class WishlistItemInGroup(BaseModel):
    """Wishlist item as shown in group view."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    url: Optional[str]
    price: Optional[Decimal]
    photo_url: Optional[str]  # S3 URI (converted to presigned URL)
    rank: int
    created_at: datetime
    updated_at: datetime
    owner_name: str
    owner_email: str
    is_purchased: Optional[bool]  # Hidden from owner
    purchased_by: Optional[UUID]  # Hidden from owner
    purchased_at: Optional[datetime]


class WishlistUserGroup(BaseModel):
    """Wishlist items grouped by user."""

    userId: str
    userName: str
    items: list[WishlistItemInGroup]


class GroupDetailResponse(BaseModel):
    """Detailed group response with members and wishlists."""

    group: GroupBasicInfo
    members: list[GroupMemberResponse]
    wishlists: list[WishlistUserGroup]


# ============================================================================
# Wishlist Models
# ============================================================================


class WishlistItemBase(BaseModel):
    """Base wishlist item fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    price: Optional[Decimal] = Field(None, ge=0)
    photo_url: Optional[str] = None  # S3 URI (s3://bucket/key) - converted to presigned URL by backend


class WishlistItemCreate(WishlistItemBase):
    """Wishlist item creation request."""

    group_ids: list[UUID] = Field(default_factory=list)
    rank: int = Field(default=0, ge=0)


class WishlistItemUpdate(BaseModel):
    """Wishlist item update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    price: Optional[Decimal] = Field(None, ge=0)
    photo_url: Optional[str] = None  # S3 URI (s3://bucket/key) - converted to presigned URL by backend
    group_ids: Optional[list[UUID]] = None
    rank: Optional[int] = Field(None, ge=0)


class WishlistItemReorderRequest(BaseModel):
    """Reorder wishlist items request."""

    items: list[dict[str, UUID | int]] = Field(..., min_length=1)


class GroupInfo(BaseModel):
    """Basic group information for wishlist items."""

    id: UUID
    name: str


class WishlistItemResponse(WishlistItemBase):
    """Wishlist item response."""

    id: UUID
    user_id: UUID
    rank: int
    groups: list[GroupInfo]
    created_at: datetime
    updated_at: datetime
    is_purchased: Optional[bool] = None  # Only visible to non-owners
    purchased_by: Optional[UUID] = None  # Only visible to non-owners


class WishlistItemWithOwner(WishlistItemResponse):
    """Wishlist item with owner info (for group views)."""

    owner_name: str
    owner_email: EmailStr


# ============================================================================
# Purchase Models
# ============================================================================


class PurchaseCreate(BaseModel):
    """Purchase creation request."""

    item_id: UUID
    group_id: UUID


class PurchaseResponse(BaseModel):
    """Purchase response."""

    id: UUID
    item_id: UUID
    purchased_by: UUID
    group_id: UUID
    purchased_at: datetime


# ============================================================================
# Invitation Models
# ============================================================================


class InvitationCreate(BaseModel):
    """Invitation creation request."""

    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class InviterInfo(BaseModel):
    """Inviter information."""

    name: str
    email: EmailStr


class InvitationResponse(BaseModel):
    """Invitation details."""

    group_id: UUID
    group_name: str
    group_description: Optional[str]
    invited_by: InviterInfo
    role: str
    expires_at: datetime


class InvitationAcceptResponse(BaseModel):
    """Invitation acceptance response."""

    group_id: UUID
    already_member: bool


# ============================================================================
# Photo Models
# ============================================================================


class PhotoUploadResponse(BaseModel):
    """Photo upload response."""

    url: HttpUrl


class PresignedUrlResponse(BaseModel):
    """Presigned URL response."""

    upload_url: HttpUrl
    file_url: HttpUrl


# ============================================================================
# Link Preview Models
# ============================================================================


class LinkPreviewResponse(BaseModel):
    """Link preview response."""

    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[HttpUrl] = None
    price: Optional[str] = None


# ============================================================================
# User Authentication Model
# ============================================================================


class AuthenticatedUser(BaseModel):
    """Authenticated user from Cognito JWT."""

    sub: UUID  # Cognito User Sub
    email: EmailStr
    name: Optional[str] = None
