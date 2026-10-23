import type { ComponentProps } from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva('button', {
  variants: { variant: { primary: 'button-primary', secondary: 'button-secondary' } },
  defaultVariants: { variant: 'primary' },
})
export function Button({ asChild = false, variant = 'primary', className, ...props }: ComponentProps<'button'> & { asChild?: boolean; variant?: 'primary' | 'secondary' }) {
  const Comp = asChild ? Slot : 'button'
  return <Comp className={cn(buttonVariants({ variant }), className)} {...props} />
}
