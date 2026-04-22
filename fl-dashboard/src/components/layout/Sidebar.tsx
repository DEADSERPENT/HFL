import React from 'react';
import clsx from 'clsx';
import {
  LayoutDashboard, Users, Play, FlaskConical,
  ScrollText, Settings, ChevronLeft, ChevronRight,
  Activity,
} from 'lucide-react';
import { useFLStore } from '../../store/useFLStore';
import { Page } from '../../types';

const navItems: { id: Page; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { id: 'clients',     label: 'Clients',     icon: Users },
  { id: 'training',    label: 'Training',    icon: Play },
  { id: 'experiments', label: 'Experiments', icon: FlaskConical },
  { id: 'logs',        label: 'Logs',        icon: ScrollText },
  { id: 'settings',    label: 'Settings',    icon: Settings },
];

export function Sidebar() {
  const { currentPage, sidebarCollapsed, setPage, toggleSidebar, isTraining } = useFLStore();

  return (
    <aside
      className={clsx(
        'sidebar-transition flex flex-col border-r border-fl-border bg-fl-panel h-full shrink-0 z-20',
        sidebarCollapsed ? 'w-14' : 'w-52',
      )}
    >
      {/* Logo */}
      <div className={clsx(
        'flex items-center gap-2.5 border-b border-fl-border shrink-0',
        sidebarCollapsed ? 'px-0 justify-center h-14' : 'px-4 h-14',
      )}>
        <div className="w-7 h-7 rounded-md bg-fl-primary flex items-center justify-center shrink-0">
          <Activity size={14} color="white" strokeWidth={2.5} />
        </div>
        {!sidebarCollapsed && (
          <div>
            <p className="text-[13px] font-semibold text-fl-text leading-none">FedVision</p>
            <p className="text-[9px] text-fl-subtle mt-0.5 leading-none uppercase tracking-wider">FL Dashboard</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {navItems.map(({ id, label, icon: Icon }) => {
          const active = currentPage === id;
          return (
            <button
              key={id}
              onClick={() => setPage(id)}
              title={sidebarCollapsed ? label : undefined}
              className={clsx(
                'w-full flex items-center gap-3 transition-all duration-150 relative',
                sidebarCollapsed ? 'justify-center px-0 py-2.5 mx-auto' : 'px-4 py-2',
                active
                  ? 'text-fl-primary bg-blue-50'
                  : 'text-fl-muted hover:text-fl-text hover:bg-fl-secondary',
              )}
            >
              {active && (
                <span className="absolute left-0 top-1 bottom-1 w-0.5 bg-fl-primary rounded-r" />
              )}
              <Icon size={16} strokeWidth={active ? 2.5 : 2} className="shrink-0" />
              {!sidebarCollapsed && (
                <span className={clsx('text-[13px] font-medium', active && 'text-fl-primary')}>
                  {label}
                </span>
              )}
              {/* Training badge */}
              {id === 'training' && isTraining && !sidebarCollapsed && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-fl-green training-dot" />
              )}
              {id === 'training' && isTraining && sidebarCollapsed && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-fl-green training-dot" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-fl-border p-2 shrink-0">
        <button
          onClick={toggleSidebar}
          className={clsx(
            'w-full flex items-center gap-2 text-fl-muted hover:text-fl-text hover:bg-fl-secondary rounded-md py-2 transition-colors',
            sidebarCollapsed ? 'justify-center px-0' : 'px-2',
          )}
        >
          {sidebarCollapsed
            ? <ChevronRight size={15} />
            : <><ChevronLeft size={15} /><span className="text-xs">Collapse</span></>
          }
        </button>
      </div>
    </aside>
  );
}
