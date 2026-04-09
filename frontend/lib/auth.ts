'use client';

import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
  ISignUpResult,
  CognitoUserSession,
} from 'amazon-cognito-identity-js';

// Check if we're in local development mode
const isLocalDev = process.env.NEXT_PUBLIC_API_URL?.includes('localhost');

// Lazy-load user pool to ensure env vars are available
let userPool: CognitoUserPool | null = null;

function getUserPool(): CognitoUserPool {
  if (!userPool) {
    const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;
    const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;

    if (!userPoolId || !clientId) {
      throw new Error('Cognito configuration is missing. Please check environment variables.');
    }

    userPool = new CognitoUserPool({
      UserPoolId: userPoolId,
      ClientId: clientId,
    });
  }
  return userPool;
}

export interface SignUpParams {
  email: string;
  password: string;
  name: string;
}

export interface SignInParams {
  email: string;
  password: string;
}

export interface ConfirmSignUpParams {
  email: string;
  code: string;
}

/**
 * Sign up a new user
 */
export function signUp({ email, password, name }: SignUpParams): Promise<ISignUpResult> {
  return new Promise((resolve, reject) => {
    const attributeList = [
      new CognitoUserAttribute({ Name: 'email', Value: email }),
      new CognitoUserAttribute({ Name: 'name', Value: name }),
    ];

    getUserPool().signUp(email, password, attributeList, [], (err, result) => {
      if (err) {
        reject(err);
      } else if (result) {
        resolve(result);
      } else {
        reject(new Error('Sign up failed'));
      }
    });
  });
}

/**
 * Confirm user sign up with code sent via email
 */
export function confirmSignUp({ email, code }: ConfirmSignUpParams): Promise<any> {
  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: getUserPool(),
    });

    cognitoUser.confirmRegistration(code, true, (err, result) => {
      if (err) {
        reject(err);
      } else {
        resolve(result);
      }
    });
  });
}

/**
 * Resend confirmation code
 */
export function resendConfirmationCode(email: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: getUserPool(),
    });

    cognitoUser.resendConfirmationCode((err, result) => {
      if (err) {
        reject(err);
      } else {
        resolve(result);
      }
    });
  });
}

/**
 * Sign in a user
 * In local dev mode, accepts any email and stores a local token
 */
export function signIn({ email, password }: SignInParams): Promise<CognitoUserSession | any> {
  // Local development mode: Accept any email and create local session
  if (isLocalDev) {
    return new Promise((resolve) => {
      // Extract username from email (e.g., alice@example.com -> alice)
      const username = email.split('@')[0];
      const localToken = `local-${username}`;

      // Store in localStorage for persistence
      localStorage.setItem('localAuthToken', localToken);
      localStorage.setItem('localAuthEmail', email);

      // Return a mock session object
      resolve({
        isValid: () => true,
        getIdToken: () => ({
          getJwtToken: () => localToken,
        }),
      } as any);
    });
  }

  // Production: Use Cognito
  return new Promise((resolve, reject) => {
    const authenticationDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: getUserPool(),
    });

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (session) => {
        resolve(session);
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: (userAttributes) => {
        reject(new Error('New password required'));
      },
    });
  });
}

/**
 * Sign out the current user
 */
export function signOut(): void {
  if (isLocalDev) {
    localStorage.removeItem('localAuthToken');
    localStorage.removeItem('localAuthEmail');
    return;
  }

  const cognitoUser = getUserPool().getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
  }
}

/**
 * Get the current user
 */
export function getCurrentUser(): CognitoUser | null {
  return getUserPool().getCurrentUser();
}

/**
 * Get the current user's session
 */
export function getCurrentSession(): Promise<CognitoUserSession | null> {
  return new Promise((resolve) => {
    const cognitoUser = getCurrentUser();
    if (!cognitoUser) {
      resolve(null);
      return;
    }

    cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
      if (err) {
        // Don't reject - just resolve with null for invalid/expired sessions
        resolve(null);
      } else if (session && session.isValid()) {
        resolve(session);
      } else {
        resolve(null);
      }
    });
  });
}

/**
 * Get the current user's JWT token
 */
export async function getAuthToken(): Promise<string | null> {
  // Local development mode: Return token from localStorage
  if (isLocalDev) {
    return localStorage.getItem('localAuthToken');
  }

  try {
    const session = await getCurrentSession();
    if (session) {
      return session.getIdToken().getJwtToken();
    }
    return null;
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
}

/**
 * Get current user attributes
 */
export function getUserAttributes(): Promise<Record<string, string>> {
  return new Promise((resolve, reject) => {
    const cognitoUser = getCurrentUser();
    if (!cognitoUser) {
      reject(new Error('No current user'));
      return;
    }

    cognitoUser.getUserAttributes((err, attributes) => {
      if (err) {
        reject(err);
      } else if (attributes) {
        const attributesMap: Record<string, string> = {};
        attributes.forEach((attr) => {
          attributesMap[attr.Name] = attr.Value;
        });
        resolve(attributesMap);
      } else {
        resolve({});
      }
    });
  });
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  // Local development mode: Check localStorage
  if (isLocalDev) {
    return localStorage.getItem('localAuthToken') !== null;
  }

  try {
    const session = await getCurrentSession();
    return session !== null && session.isValid();
  } catch (error) {
    return false;
  }
}

/**
 * Initiate forgot password flow — sends a reset code to the user's email
 */
export function forgotPassword(email: string): Promise<void> {
  if (isLocalDev) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({ Username: email, Pool: getUserPool() });
    cognitoUser.forgotPassword({
      onSuccess: () => resolve(),
      onFailure: (err) => reject(err),
    });
  });
}

/**
 * Complete forgot password flow — applies new password using the emailed reset code
 */
export function confirmForgotPassword(email: string, code: string, newPassword: string): Promise<void> {
  if (isLocalDev) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({ Username: email, Pool: getUserPool() });
    cognitoUser.confirmPassword(code, newPassword, {
      onSuccess: () => resolve(),
      onFailure: (err) => reject(err),
    });
  });
}

/**
 * Change the current user's password
 */
export function changePassword(oldPassword: string, newPassword: string): Promise<string> {
  // Local development mode: Just pretend it worked
  if (isLocalDev) {
    return Promise.resolve('SUCCESS');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = getCurrentUser();
    if (!cognitoUser) {
      reject(new Error('No current user'));
      return;
    }

    // Need to get the session first to ensure user is authenticated
    cognitoUser.getSession((sessionErr: Error | null, session: CognitoUserSession | null) => {
      if (sessionErr || !session || !session.isValid()) {
        console.error('Session error:', sessionErr);
        reject(new Error('User is not authenticated'));
        return;
      }

      console.log('Session is valid, attempting password change...');
      // Now change the password
      cognitoUser.changePassword(oldPassword, newPassword, (err, result) => {
        if (err) {
          console.error('Cognito changePassword error:', err);
          reject(err);
        } else {
          console.log('Password changed successfully');
          resolve(result ?? 'SUCCESS');
        }
      });
    });
  });
}
