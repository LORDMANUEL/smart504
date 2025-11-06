'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { users as usersApi, UpdateUserDto, UserRole, User } from '@ecommerce/sdk';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, CardFooter } from '@ecommerce/ui';

export default function EditUserPage() {
  const [user, setUser] = useState<User | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.VENTAS);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await usersApi.getOne(id);
        setUser(userData);
        setName(userData.name);
        setEmail(userData.email);
        setRole(userData.role);
      } catch (err) {
        setError('Failed to fetch user data.');
      }
    };
    if (id) {
      fetchUser();
    }
  }, [id]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const userData: UpdateUserDto = { name, email, role };

    try {
      await usersApi.update(id, userData);
      router.push('/dashboard/users');
    } catch (err) {
      setError('Failed to update user.');
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      setIsLoading(true);
      setError(null);
      try {
        await usersApi.delete(id);
        router.push('/dashboard/users');
      } catch (err) {
        setError('Failed to delete user.');
        setIsLoading(false);
      }
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Edit User: {user.name}</CardTitle>
      </CardHeader>
      <form onSubmit={handleUpdate}>
        <CardContent className="space-y-4">
          <Input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <select value={role} onChange={(e) => setRole(e.target.value as UserRole)} className="w-full h-10 px-3 rounded-lg bg-gray-100 shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff]">
            {Object.values(UserRole).map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button type="button" variant="destructive" onClick={handleDelete} disabled={isLoading}>
            Delete User
          </Button>
          <div className="flex space-x-2">
            <Button type="button" variant="ghost" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Updating...' : 'Update User'}
            </Button>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}
