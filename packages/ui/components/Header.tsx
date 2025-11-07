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

const HeaderCart = ({ itemCount }: { itemCount: number }) => (
    <Link href="/carrito" className="relative">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        {itemCount > 0 && (
            <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {itemCount}
            </span>
        )}
    </Link>
);


export { Header, HeaderTitle, HeaderNav, HeaderCart };
