'use client';

import { AdminLayout } from '@ecommerce/ui';
import { Sidebar } from '../../components/Sidebar';
import withAuth from '../../hoc/withAuth';

function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminLayout sidebar={<Sidebar />}>
      {children}
    </AdminLayout>
  );
}

export default withAuth(DashboardLayout);
