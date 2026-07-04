import {
  BookOpen,
  Bot,
  ChevronLeft,
  ChevronRight,
  Code2,
  Filter,
  FlaskConical,
  HelpCircle,
  Inbox,
  LayoutDashboard,
  List,
  Mail,
  MessageCircleReply,
  PenSquare,
  Search,
  Server,
  Settings,
  Users,
  Wrench,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/common/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/inbox", label: "Inbox", icon: Inbox },
    { href: "/mail", label: "Mail Reader", icon: Mail },
    { href: "/search", label: "Search", icon: Search },
    { href: "/compose", label: "Compose", icon: PenSquare },
    { href: "/chat", label: "AI Chat", icon: Bot },
    { href: "/lab", label: "Mail Lab", icon: FlaskConical },
    { href: "/services", label: "Services", icon: Server },
    { href: "/contacts", label: "Contacts", icon: Users },
    { href: "/auto-respond", label: "Auto-Reply", icon: MessageCircleReply },
    { href: "/rules", label: "Rules", icon: Filter },
    { href: "/logs", label: "Logs", icon: List },
    { href: "/tools", label: "Tools", icon: Wrench },
    { href: "/skill", label: "Skill", icon: BookOpen },
    { href: "/api-docs", label: "API Docs", icon: Code2 },
    { href: "/help", label: "Help", icon: HelpCircle },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-16 items-center border-b border-slate-800 px-4">
        <div className="flex items-center gap-2 font-semibold text-slate-100">
          <Mail className="h-6 w-6 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300">Email Hub</span>
          )}
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                isActive ? "bg-slate-800 text-white" : "text-slate-400",
                collapsed ? "justify-center" : "justify-start",
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  !collapsed && "mr-3",
                  isActive && "text-blue-400",
                )}
              />
              {!collapsed && <span>{item.label}</span>}

              {collapsed && (
                <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 p-2">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <div className="flex items-center w-full">
              <ChevronLeft className="h-5 w-5 mr-3" />
              <span>Collapse</span>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}
