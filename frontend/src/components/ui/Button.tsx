
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "size"> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "raised" | "ghost";
  size?: "sm" | "md" | "lg";
}

export default function Button({
  children,
  variant = "primary",
  onClick,
  disabled = false,
  className = "",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center font-sans font-medium rounded-md transition-all duration-150 focus-visible:outline-2 focus-visible:outline-brass disabled:opacity-40 disabled:cursor-not-allowed select-none cursor-pointer";

  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-xs sm:text-sm gap-2",
    lg: "px-5 py-2.5 text-sm sm:text-base font-semibold gap-2.5",
  };

  const variants = {
    primary:
      "bg-brass text-night font-semibold hover:bg-[#d6b26d] active:bg-[#b8944f] border border-brass shadow-sm",
    secondary:
      "bg-surface text-parchment border border-rule hover:border-brass/70 hover:bg-raised active:bg-surface",
    raised:
      "bg-raised text-parchment border border-rule hover:border-muted/60 active:bg-surface",
    ghost:
      "text-muted hover:text-parchment hover:bg-surface/50 border border-transparent",
  };

  return (
    <button
      {...props}
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
