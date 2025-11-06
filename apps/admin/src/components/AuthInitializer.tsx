'use client';

import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';

export const AuthInitializer = () => {
  const { accessToken, fetchProfile } = useAuthStore();

  useEffect(() => {
    // This is a simplified example. In a real app, you'd likely check
    // for a token stored in localStorage or an httpOnly cookie.
    // For now, we just fetch the profile if a token exists in the store.
    if (accessToken) {
      fetchProfile();
    }
  }, [accessToken, fetchProfile]);

  return null; // This component doesn't render anything
};
