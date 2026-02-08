// Profile types
export interface Profile {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
}

// Group types
export interface GroupInfo {
  id: string;
  name: string;
}

export interface Group {
  id: string;
  name: string;
  description?: string;
  role: 'admin' | 'member';
  member_count: number;
  created_at: string;
}

export interface GroupCreate {
  name: string;
  description?: string;
}

export interface GroupMember {
  user_id: string;
  name: string;
  email: string;
  role: 'admin' | 'member';
  joined_at: string;
}

export interface GroupDetail {
  group: {
    id: string;
    name: string;
    description?: string;
    created_by: string;
    created_at: string;
  };
  members: GroupMember[];
  wishlists: MemberWishlist[];
}

export interface MemberWishlist {
  user_id: string;
  user_name: string;
  items: WishlistItem[];
}

// Wishlist types
export interface WishlistItem {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  url?: string;
  price?: number;
  photo_url?: string;
  rank: number;
  groups: GroupInfo[];
  created_at: string;
  updated_at: string;
  is_purchased?: boolean;  // Hidden if viewing own items
  purchased_by?: string;    // Hidden if viewing own items
}

export interface WishlistItemCreate {
  name: string;
  description?: string;
  url?: string;
  price?: number;
  photo_url?: string;
  rank?: number;
  group_ids: string[];
}

export interface WishlistItemUpdate {
  name?: string;
  description?: string | null;
  url?: string | null;
  price?: number | null;
  photo_url?: string | null;
  rank?: number;
  group_ids?: string[];
}

export interface WishlistReorderItem {
  id: string;
  rank: number;
}

// Purchase types
export interface Purchase {
  id: string;
  item_id: string;
  purchased_by: string;
  group_id: string;
  purchased_at: string;
}

export interface PurchaseCreate {
  item_id: string;
  group_id: string;
}

// Invitation types
export interface Invitation {
  group_id: string;
  group_name: string;
  group_description?: string;
  invited_by: {
    name: string;
    email?: string;  // Optional now
  };
  role: 'admin' | 'member';
  expires_at?: string;  // Optional now
  max_uses?: number;
  current_uses: number;
  is_expired: boolean;
  is_full: boolean;
}

export interface InvitationCreate {
  role?: 'admin' | 'member';
  max_uses?: number;       // null = unlimited
  expires_in_days?: number; // null = never expires
}

export interface InvitationResponse {
  invite_url: string;
  max_uses?: number;
  current_uses: number;
  expires_at?: string;
}

export interface ActiveInvitation {
  token: string;
  invite_url: string;
  created_by: string;
  created_at: string;
  expires_at?: string;
  max_uses?: number;
  current_uses: number;
  accepted_by: Array<{
    name: string;
    accepted_at: string;
  }>;
}
