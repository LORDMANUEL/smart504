'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@ecommerce/ui';

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/dashboard/users', label: 'Users' },
  // Add other navigation items here
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col space-y-2">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            'px-3 py-2 rounded-lg text-sm font-medium',
            pathname === item.href
              ? 'bg-gray-300 text-gray-900 shadow-inner'
              : 'text-gray-700 hover:bg-gray-200'
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
