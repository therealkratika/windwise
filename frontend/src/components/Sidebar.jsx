import {
  BarChart3,
  CalendarDays,
  LayoutDashboard,
  Settings2,
  Wind,
} from 'lucide-react'

const navigation = [
  { label: 'Overview', icon: LayoutDashboard, active: true },
  { label: 'Forecasts', icon: BarChart3 },
  { label: 'Periods', icon: CalendarDays },
]

function Sidebar() {
  return (
    <aside className="flex w-full shrink-0 flex-col bg-[#12343b] p-[14px_16px] text-[#d8e7e9] sm:w-[200px] sm:p-[28px_16px_20px] lg:w-[240px]">
      <div className="flex items-center gap-2.5 px-1 pb-[14px] font-display text-[21px] font-bold text-white sm:px-3 sm:pb-[42px]">
        <span className="grid size-[34px] place-items-center rounded-[9px] bg-[#2e9cac]">
          <Wind size={20} strokeWidth={2.5} />
        </span>
        <span>WindWise</span>
      </div>

      <nav aria-label="Main navigation">
        <p className="mx-3 mb-3 hidden text-[10px] font-bold uppercase tracking-[.09em] text-[#7da2a8] sm:block">Workspace</p>
        {navigation.map(({ label, icon: Icon, active }) => (
          <a
            className={`flex items-center gap-3 rounded-lg px-3 py-[11px] text-sm font-medium ${active ? 'bg-[#1d4d55] text-white' : 'hidden text-[#a8c2c5] hover:bg-[#1d4d55] hover:text-white'} sm:flex ${active ? 'flex-1 sm:flex-none' : ''}`}
            href={`#${label.toLowerCase()}`}
            key={label}
            aria-current={active ? 'page' : undefined}
          >
            <Icon size={18} />
            {label}
          </a>
        ))}
      </nav>

      <div className="mt-auto hidden sm:block">
        <a className="flex items-center gap-3 rounded-lg px-3 py-[11px] text-sm font-medium text-[#a8c2c5] hover:bg-[#1d4d55] hover:text-white" href="#settings">
          <Settings2 size={18} />
          Settings
        </a>
        <div className="mt-6 flex items-center gap-[9px] border-t border-[#2b5960] px-2.5 py-3.5 text-xs">
          <span className="size-[7px] rounded-full bg-[#40c98a] shadow-[0_0_0_3px_rgba(64,201,138,.15)]" />
          <span>
            <span><strong className="block text-[11px] text-[#d8e7e9]">Data connection</strong><small className="mt-[3px] block text-[#7da2a8]">Elexon BMRS</small></span>
          </span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
