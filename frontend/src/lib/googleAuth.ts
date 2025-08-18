// Google Sign-In service utilities
import { signInWithPopup, signInWithRedirect, getRedirectResult } from 'firebase/auth';
import type { User } from 'firebase/auth';
import { auth, googleProvider } from './firebase';

export interface GoogleSignInResult {
  success: boolean;
  user?: User;
  idToken?: string;
  error?: string;
}

/**
 * Sign in with Google using popup
 */
export const signInWithGooglePopup = async (): Promise<GoogleSignInResult> => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    
    // Get the ID token
    const idToken = await user.getIdToken();
    
    return {
      success: true,
      user,
      idToken
    };
  } catch (error: any) {
    console.error('Google Sign-In error:', error);
    
    // Handle specific error codes
    let errorMessage = 'Failed to sign in with Google';
    
    if (error.code === 'auth/popup-closed-by-user') {
      errorMessage = 'Sign-in was cancelled';
    } else if (error.code === 'auth/popup-blocked') {
      errorMessage = 'Pop-up was blocked by the browser';
    } else if (error.code === 'auth/cancelled-popup-request') {
      errorMessage = 'Sign-in was cancelled';
    } else if (error.code === 'auth/account-exists-with-different-credential') {
      errorMessage = 'An account already exists with the same email address but different sign-in credentials';
    }
    
    return {
      success: false,
      error: errorMessage
    };
  }
};

/**
 * Sign in with Google using redirect (recommended for mobile)
 */
export const signInWithGoogleRedirect = async (): Promise<void> => {
  try {
    await signInWithRedirect(auth, googleProvider);
  } catch (error: any) {
    console.error('Google Sign-In redirect error:', error);
    throw error;
  }
};

/**
 * Get redirect result after sign-in redirect
 */
export const getGoogleRedirectResult = async (): Promise<GoogleSignInResult> => {
  try {
    const result = await getRedirectResult(auth);
    
    if (result && result.user) {
      // Get the ID token
      const idToken = await result.user.getIdToken();
      
      return {
        success: true,
        user: result.user,
        idToken
      };
    }
    
    return {
      success: false,
      error: 'No redirect result available'
    };
  } catch (error: any) {
    console.error('Google redirect result error:', error);
    
    let errorMessage = 'Failed to process Google sign-in';
    
    if (error.code === 'auth/account-exists-with-different-credential') {
      errorMessage = 'An account already exists with the same email address but different sign-in credentials';
    }
    
    return {
      success: false,
      error: errorMessage
    };
  }
};

/**
 * Check if the current device is mobile
 */
export const isMobile = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

/**
 * Sign in with Google using the appropriate method based on device
 */
export const signInWithGoogle = async (): Promise<GoogleSignInResult> => {
  if (isMobile()) {
    // Use redirect for mobile devices
    await signInWithGoogleRedirect();
    return { success: true }; // The actual result will be handled by getGoogleRedirectResult
  } else {
    // Use popup for desktop
    return await signInWithGooglePopup();
  }
};
