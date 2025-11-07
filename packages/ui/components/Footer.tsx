import * as React from 'react';
import { cn } from '../lib/utils';

const Footer = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => (
  <footer
    ref={ref}
    className={cn('py-6 md:px-8 md:py-0 bg-gray-200', className)}
    {...props}
  >
    <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
      <p className="text-center text-sm leading-loose text-gray-600 md:text-left">
        © {new Date().getFullYear()} E-Commerce de Repuestos. All rights reserved.
      </p>
    </div>
  </footer>
));
Footer.displayName = 'Footer';

export { Footer };
