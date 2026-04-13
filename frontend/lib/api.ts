'use client';

import axios, { AxiosInstance, AxiosError } from 'axios';
import { getAuthToken } from './auth';
import type {
  Profile,
  Group,
  GroupCreate,
  GroupDetail,
  WishlistItem,
  WishlistItemCreate,
  WishlistItemUpdate,
  WishlistReorderItem,
  Purchase,
  PurchaseCreate,
  Invitation,
  InvitationCreate,
  InvitationResponse,
  ActiveInvitation,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL environment variable is not set');
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to attach JWT token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error
          const status = error.response.status;
          const data = error.response.data as any;

          if (status === 401) {
            // Unauthorized - redirect to login
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/login';
            }
          }

          return Promise.reject({
            message: data?.detail || data?.error || data?.message || 'An error occurred',
            statusCode: status,
          });
        } else if (error.request) {
          // Request made but no response
          return Promise.reject({
            message: 'No response from server',
            statusCode: 0,
          });
        } else {
          // Error setting up request
          return Promise.reject({
            message: error.message,
            statusCode: 0,
          });
        }
      }
    );
  }

  // Profile endpoints
  async getProfile(): Promise<Profile> {
    const response = await this.client.get<Profile>('/profile');
    return response.data;
  }

  async updateProfile(name: string): Promise<Profile> {
    const response = await this.client.put<Profile>('/profile', { name });
    return response.data;
  }

  // Group endpoints
  async getGroups(): Promise<{ groups: Group[] }> {
    const response = await this.client.get<{ groups: Group[] }>('/groups');
    return response.data;
  }

  async createGroup(data: GroupCreate): Promise<Group> {
    const response = await this.client.post<Group>('/groups', data);
    return response.data;
  }

  async getGroup(id: string): Promise<GroupDetail> {
    const response = await this.client.get<GroupDetail>(`/groups/${id}`);
    return response.data;
  }

  async deleteGroup(id: string): Promise<void> {
    await this.client.delete(`/groups/${id}`);
  }

  async createInvitation(groupId: string, data: InvitationCreate = {}): Promise<InvitationResponse> {
    const response = await this.client.post<InvitationResponse>(`/groups/${groupId}/members`, data);
    return response.data;
  }

  async getActiveInvitations(groupId: string): Promise<ActiveInvitation[]> {
    const response = await this.client.get<ActiveInvitation[]>(`/groups/${groupId}/invitations/active`);
    return response.data;
  }

  async revokeInvitation(token: string): Promise<void> {
    await this.client.delete(`/invitations/${token}/revoke`);
  }

  async removeMember(groupId: string, userId: string): Promise<void> {
    await this.client.delete(`/groups/${groupId}/members/${userId}`);
  }

  // Wishlist endpoints
  async getWishlist(): Promise<{ items: WishlistItem[] }> {
    const response = await this.client.get<{ items: WishlistItem[] }>('/wishlist');
    return response.data;
  }

  async createWishlistItem(data: WishlistItemCreate): Promise<WishlistItem> {
    const response = await this.client.post<WishlistItem>('/wishlist', data);
    return response.data;
  }

  async updateWishlistItem(id: string, data: WishlistItemUpdate): Promise<WishlistItem> {
    const response = await this.client.put<WishlistItem>(`/wishlist/${id}`, data);
    return response.data;
  }

  async deleteWishlistItem(id: string): Promise<void> {
    await this.client.delete(`/wishlist/${id}`);
  }

  async reorderWishlistItems(items: WishlistReorderItem[]): Promise<{ success: boolean }> {
    const response = await this.client.put<{ success: boolean }>('/wishlist/reorder', { items });
    return response.data;
  }

  // Purchase endpoints
  async claimItem(data: PurchaseCreate): Promise<Purchase> {
    const response = await this.client.post<Purchase>('/purchases', data);
    return response.data;
  }

  async unclaimItem(itemId: string, groupId: string): Promise<void> {
    await this.client.delete(`/purchases/${itemId}/${groupId}`);
  }

  // Invitation endpoints
  async getInvitation(token: string): Promise<Invitation> {
    const response = await this.client.get<Invitation>(`/invitations/${token}`);
    return response.data;
  }

  async acceptInvitation(token: string): Promise<{ group_id: string; already_member: boolean }> {
    const response = await this.client.post<{ group_id: string; already_member: boolean }>(
      `/invitations/${token}/accept`
    );
    return response.data;
  }

  // Photo upload endpoint - get presigned S3 URL
  async getPhotoUploadUrl(): Promise<{ upload_url: string; fields: Record<string, string>; file_url: string; preview_url: string }> {
    const response = await this.client.post<{ upload_url: string; fields: Record<string, string>; file_url: string; preview_url: string }>('/photos/upload');
    return response.data;
  }

  // Upload photo directly to S3 using presigned URL
  async uploadPhotoToS3(uploadUrl: string, fields: Record<string, string>, file: File): Promise<void> {
    const formData = new FormData();

    // Add presigned POST fields first
    Object.entries(fields).forEach(([key, value]) => {
      formData.append(key, value);
    });

    // Add file last
    formData.append('file', file);

    // Upload directly to S3 (no auth token needed)
    await axios.post(uploadUrl, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async markReceived(itemId: string): Promise<WishlistItem> {
    const response = await this.client.patch<WishlistItem>(`/wishlist/${itemId}/received`);
    return response.data;
  }

  async submitFeedback(title: string | undefined, body: string): Promise<{ issue_url: string }> {
    const response = await this.client.post<{ issue_url: string }>('/feedback', { title, body });
    return response.data;
  }

  // Convenience aliases
  createItem = this.createWishlistItem;
  updateItem = this.updateWishlistItem;
  deleteItem = this.deleteWishlistItem;
  reorderItems = this.reorderWishlistItems;
}

// Export singleton instance
export const api = new ApiClient();
