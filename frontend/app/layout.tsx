import type { Metadata } from "next";
import Link from "next/link";
import { LayoutDashboard, Settings, TrendingUp, BarChart3 } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "AURUM Dashboard",
  description: "黄金量化交易系统 - 多代理AI策略",
  icons: { icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🥇</text></svg>" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-okx-bg">
        <div className="flex h-screen">
          {/* 侧边栏 */}
          <aside className="w-64 bg-okx-card border-r border-okx-border flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-okx-border">
              <h1 className="text-xl font-bold text-okx-gold">AURUM</h1>
              <p className="text-xs text-okx-muted mt-1">量化交易系统</p>
            </div>

            {/* 导航菜单 */}
            <nav className="flex-1 p-4 space-y-2">
              <NavLink href="/dashboard" icon={<LayoutDashboard className="w-5 h-5" />}>
                Dashboard
              </NavLink>
              <NavLink href="/strategies" icon={<Settings className="w-5 h-5" />}>
                策略配置
              </NavLink>
              <NavLink href="/backtest" icon={<BarChart3 className="w-5 h-5" />}>
                回测结果
              </NavLink>
              <NavLink href="/analytics" icon={<TrendingUp className="w-5 h-5" />}>
                数据分析
              </NavLink>
            </nav>

            {/* 底部信息 */}
            <div className="p-4 border-t border-okx-border">
              <div className="text-xs text-okx-dim">
                <p>© 2026 AURUM</p>
                <p className="mt-1">v3.0.0</p>
              </div>
            </div>
          </aside>

          {/* 主内容区 */}
          <main className="flex-1 overflow-auto">
            <div className="p-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, icon, children }: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-3 rounded-lg text-okx-muted hover:text-okx-text hover:bg-okx-hover transition-colors"
    >
      {icon}
      <span className="font-medium">{children}</span>
    </Link>
  );
}



