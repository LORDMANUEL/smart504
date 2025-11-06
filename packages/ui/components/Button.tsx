import * as React from 'react';
import { tv, type VariantProps } from 'tailwind-variants';
import { cn } from '../lib/utils';

const buttonVariants = tv({
  base: 'inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
  variants: {
    variant: {
      default:
        'bg-gray-100 text-gray-800 shadow-[5px_5px_10px_#bebebe,-5px_-5px_10px_#ffffff] hover:shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff] active:shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff]',
      primary:
        'bg-blue-500 text-white shadow-[5px_5px_10px_#3d8bf2,-5px_-5px_10px_#4b9bff] hover:bg-blue-600',
      destructive:
        'bg-red-500 text-white shadow-[5px_5px_10px_#f23d3d,-5px_-5px_10px_#ff4b4b] hover:bg-red-600',
      ghost: 'bg-transparent text-gray-800 hover:bg-gray-200',
    },
    size: {
      default: 'h-10 px-4 py-2',
      sm: 'h-9 rounded-md px-3',
      lg: 'h-11 rounded-md px-8',
      icon: 'h-10 w-10',
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'default',
  },
});

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
