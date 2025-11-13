'use client';

import withAuth from '../hoc/withAuth';
import { useAuthStore } from '../stores/authStore';
import { Button, Card, CardHeader, CardTitle, CardContent } from '@ecommerce/ui';

function DashboardPage() {
  const { user, logout } = useAuthStore();

  return (
    <div className="p-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Welcome, {user?.name}</CardTitle>
          <Button onClick={logout} variant="destructive">Logout</Button>
        </CardHeader>
        <CardContent>
          <p>Email: {user?.email}</p>
          <p>Role: {user?.role}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default withAuth(DashboardPage);
