import { ButtonHTMLAttributes, InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border border-border-hairline bg-surface-card shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function Button({
  className = "",
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  const styles: Record<string, string> = {
    primary: "bg-series-1 text-white hover:opacity-90",
    secondary: "bg-surface-raised border border-border-strong text-text-primary hover:bg-surface-page",
    danger: "bg-status-critical text-white hover:opacity-90",
    ghost: "text-text-secondary hover:bg-surface-page",
  };
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-lg border border-border-strong bg-surface-raised px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-series-1 focus:outline-none focus:ring-1 focus:ring-series-1 ${className}`}
      {...props}
    />
  );
}

export function Select({ className = "", children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`rounded-lg border border-border-strong bg-surface-raised px-3 py-2 text-sm text-text-primary focus:border-series-1 focus:outline-none focus:ring-1 focus:ring-series-1 ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1.5 block text-sm font-medium text-text-secondary">{children}</label>;
}

export function ErrorText({ children }: { children: ReactNode }) {
  return <p className="text-sm text-status-critical">{children}</p>;
}

export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-semibold text-text-primary">{title}</h1>
      {description && <p className="mt-1 text-sm text-text-secondary">{description}</p>}
    </div>
  );
}
