'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { users as usersApi, CreateUserDto, UserRole } from '@ecommerce/sdk';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, CardFooter } from '@ecommerce/ui';

export default function NewUserPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.VENTAS);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const userData: CreateUserDto = { name, email, password, role };

    try {
      await usersApi.create(userData);
      router.push('/dashboard/users');
    } catch (err) {
      setError('Failed to create user. Please check the details.');
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New User</CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
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
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <select value={role} onChange={(e) => setRole(e.target.value as UserRole)} className="w-full h-10 px-3 rounded-lg bg-gray-100 shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff]">
            {Object.values(UserRole).map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </CardContent>
        <CardFooter className="flex justify-end space-x-2">
          <Button type="button" variant="ghost" onClick={() => router.back()}>Cancel</Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create User'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
