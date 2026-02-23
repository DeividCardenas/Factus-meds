import Link from "next/link";
import { FileText, ClipboardList, LayoutDashboard } from "lucide-react";

const navItems = [
  { href: "/invoices", label: "Facturas", icon: FileText },
  { href: "/audit", label: "Auditoría", icon: ClipboardList },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-64 flex-col bg-gray-900 text-gray-100">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-700">
        <LayoutDashboard className="h-6 w-6 text-indigo-400" />
        <span className="text-lg font-semibold tracking-tight">Factus Meds</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
