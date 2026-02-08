'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CognitoUserSession } from 'amazon-cognito-identity-js';
import {
  signIn as authSignIn,
  signOut as authSignOut,
  signUp as authSignUp,
  confirmSignUp as authConfirmSignUp,
  resendConfirmationCode as authResendCode,
  getCurrentSession,
  getUserAttributes,
  SignInParams,
  SignUpParams,
  ConfirmSignUpParams,
} from '../auth';
import type { ISignUpResult } from 'amazon-cognito-identity-js';
import { api } from '../api';
import type { Profile } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  profile: Profile | null;
  signIn: (params: SignInParams) => Promise<void>;
  signUp: (params: SignUpParams) => Promise<ISignUpResult>;
  confirmSignUp: (params: ConfirmSignUpParams) => Promise<void>;
  resendConfirmationCode: (email: string) => Promise<void>;
  signOut: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [profile, setProfile] = useState<Profile | null>(null);

  const loadSession = async () => {
    try {
      const session = await getCurrentSession();
      if (session && session.isValid()) {
        setIsAuthenticated(true);
        // Fetch user profile
        try {
          const profileData = await api.getProfile();
          setProfile(profileData);
        } catch (error) {
          console.error('Error fetching profile:', error);
        }
      } else {
        setIsAuthenticated(false);
        setProfile(null);
      }
    } catch (error) {
      setIsAuthenticated(false);
      setProfile(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, []);

  const signIn = async (params: SignInParams) => {
    await authSignIn(params);
    setIsAuthenticated(true);
    // Fetch profile after sign in
    try {
      const profileData = await api.getProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Error fetching profile after sign in:', error);
    }
  };

  const signUp = async (params: SignUpParams) => {
    return await authSignUp(params);
  };

  const confirmSignUp = async (params: ConfirmSignUpParams) => {
    await authConfirmSignUp(params);
  };

  const resendConfirmationCode = async (email: string) => {
    await authResendCode(email);
  };

  const signOut = () => {
    authSignOut();
    setIsAuthenticated(false);
    setProfile(null);
  };

  const refreshProfile = async () => {
    try {
      const profileData = await api.getProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Error refreshing profile:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        profile,
        signIn,
        signUp,
        confirmSignUp,
        resendConfirmationCode,
        signOut,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
