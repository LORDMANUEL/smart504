'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../stores/authStore';

const withAuth = <P extends object>(WrappedComponent: React.ComponentType<P>) => {
  const Wrapper = (props: P) => {
    const router = useRouter();
    const { accessToken, isLoading } = useAuthStore();

    useEffect(() => {
      if (!isLoading && !accessToken) {
        router.replace('/login');
      }
    }, [isLoading, accessToken, router]);

    if (isLoading || !accessToken) {
      return <div>Loading...</div>; // Or a spinner component
    }

    return <WrappedComponent {...props} />;
  };

  return Wrapper;
};

export default withAuth;
