'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import withAuth from '../hoc/withAuth';

function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);

  return <div>Loading...</div>; // Or a loading spinner
}

export default withAuth(RootPage);
