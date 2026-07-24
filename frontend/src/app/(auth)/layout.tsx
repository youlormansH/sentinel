export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-page px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-2">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-series-1 text-white">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5l-8-3z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-text-primary">Sentinel</h1>
          <p className="text-sm text-text-secondary">Cloud Security &amp; Threat Detection Platform</p>
        </div>
        {children}
      </div>
    </div>
  );
}
