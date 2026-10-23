
import type { ReactNode } from "react";

interface SmallCapsProps {
  children: ReactNode;
  className?: string;
}

export default function SmallCaps({
  children,
  className = "",
}: SmallCapsProps) {
  return (
    <span
      className={`font-sans text-xs uppercase tracking-wider font-semibold text-muted/90 ${className}`}
    >
      {children}
    </span>
  );
}
