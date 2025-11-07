import * as React from 'react';
import { cn } from '../lib/utils';
import Link from 'next/link';

const Header = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, children, ...props }, ref) => (
  <header
    ref={ref}
    className={cn(
      'sticky top-0 z-50 w-full border-b border-gray-200 bg-gray-100/95 backdrop-blur supports-[backdrop-filter]:bg-gray-100/60',
      className
    )}
    {...props}
  >
    <div className="container flex h-14 items-center">{children}</div>
  </header>
));
Header.displayName = 'Header';

const HeaderTitle = ({ children }: { children: React.ReactNode }) => (
    <Link href="/" className="mr-6 flex items-center space-x-2">
        <span className="font-bold sm:inline-block">{children}</span>
    </Link>
);

const HeaderNav = ({ children }: { children: React.ReactNode }) => (
    <nav className="flex items-center gap-6 text-sm">
        {children}
    </nav>
);

export { Header, HeaderTitle, HeaderNav };
