"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Activity, FileText, Settings } from "lucide-react"

export function Nav() {
  const pathname = usePathname()

  const links = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/calls", label: "Call Logs", icon: FileText },
    { href: "/settings", label: "Settings", icon: Settings },
  ]

  return (
    <nav className="border-b border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">AL</span>
              </div>
              <span className="font-semibold text-lg">Axiom Labs</span>
              <span className="text-muted-foreground text-sm">Voice Agent</span>
            </div>
            <div className="flex gap-1">
              {links.map((link) => {
                const Icon = link.icon
                const isActive = pathname === link.href
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      isActive
                        ? "bg-accent text-accent-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
                    )}
                  >
                    <Icon className="size-4" />
                    {link.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
