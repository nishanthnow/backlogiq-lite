
interface HeaderProps {
  onLogout?: () => void
}

export default function Header({ onLogout }: HeaderProps) {
  return (
    <header className="bg-white border-b border-slate-200 shadow-sm">
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blue-600">BacklogIQ Lite</h1>
          <p className="text-sm text-slate-500">Backlog Quality Copilot</p>
        </div>
        <div className="flex items-center gap-4">
          {onLogout && (
            <button
              onClick={onLogout}
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Sign Out
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
