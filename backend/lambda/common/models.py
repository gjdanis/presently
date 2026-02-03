"""Pydantic models for request/response validation."""

from datetime import datetime
from decimal import Decimal
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

    name: str | None = Field(None, min_length=1, max_length=255)


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
    description: str | None = None


class GroupCreate(GroupBase):
    """Group creation request."""

    pass


class GroupUpdate(BaseModel):
    """Group update request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


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


class GroupInfo(BaseModel):
    """Basic group information for wishlist items."""

    id: UUID
    name: str


class WishlistItemInGroup(BaseModel):
    """Wishlist item as shown in group view."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    url: str | None
    price: Decimal | None
    photo_url: str | None  # S3 URI (converted to presigned URL)
    rank: int
    groups: list[GroupInfo]  # Include group assignments for editing
    created_at: datetime
    updated_at: datetime
    owner_name: str
    owner_email: str
    is_purchased: bool | None  # Hidden from owner
    purchased_by: UUID | None  # Hidden from owner
    purchased_at: datetime | None


class WishlistUserGroup(BaseModel):
    """Wishlist items grouped by user."""

    user_id: str
    user_name: str
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
    description: str | None = None
    url: HttpUrl | None = None
    price: Decimal | None = Field(None, ge=0)
    photo_url: str | None = None  # S3 URI (s3://bucket/key) - converted to presigned URL by backend


class WishlistItemCreate(WishlistItemBase):
    """Wishlist item creation request."""

    group_ids: list[UUID] = Field(default_factory=list)
    rank: int = Field(default=0, ge=0)


class WishlistItemUpdate(BaseModel):
    """Wishlist item update request."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    url: HttpUrl | None = None
    price: Decimal | None = Field(None, ge=0)
    photo_url: str | None = None  # S3 URI (s3://bucket/key) - converted to presigned URL by backend
    group_ids: list[UUID] | None = None
    rank: int | None = Field(None, ge=0)


class WishlistItemResponse(WishlistItemBase):
    """Wishlist item response."""

    id: UUID
    user_id: UUID
    rank: int
    groups: list[GroupInfo]
    created_at: datetime
    updated_at: datetime
    is_purchased: bool | None = None  # Only visible to non-owners
    purchased_by: UUID | None = None  # Only visible to non-owners


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
    """Multi-use invitation creation request."""

    role: str = Field(default="member", pattern="^(admin|member)$")
    max_uses: int | None = Field(default=None, ge=1)  # NULL = unlimited
    expires_in_days: int | None = Field(default=None, ge=1)


class InviterInfo(BaseModel):
    """Inviter information."""

    name: str
    email: EmailStr | None = None


class InvitationResponse(BaseModel):
    """Invitation details."""

    group_id: UUID
    group_name: str
    group_description: str | None
    invited_by: InviterInfo
    role: str
    expires_at: datetime | None = None
    max_uses: int | None = None
    current_uses: int = 0
    is_expired: bool = False
    is_full: bool = False


class InvitationAcceptResponse(BaseModel):
    """Invitation acceptance response."""

    group_id: UUID
    already_member: bool


class InvitationCreateResponse(BaseModel):
    """Multi-use invitation creation response."""

    invite_url: str
    max_uses: int | None = None
    current_uses: int = 0
    expires_at: datetime | None = None


# ============================================================================
# Photo Models
# ============================================================================


class PresignedUrlResponse(BaseModel):
    """Presigned URL response for photo upload."""

    upload_url: str
    fields: dict
    file_url: str  # S3 URI for database storage
    preview_url: str  # HTTP URL for immediate display


# ============================================================================
# User Authentication Model
# ============================================================================


class AuthenticatedUser(BaseModel):
    """Authenticated user from Cognito JWT."""

    sub: UUID  # Cognito User Sub
    email: EmailStr
    name: str | None = None
