import * as React from "react"

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline'
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: "bg-primary hover:bg-primary/80 text-primary-foreground",
      secondary: "bg-secondary hover:bg-secondary/80 text-secondary-foreground",
      destructive: "bg-destructive hover:bg-destructive/80 text-destructive-foreground",
      outline: "text-foreground border border-input"
    }
    
    return (
      <div
        ref={ref}
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus 