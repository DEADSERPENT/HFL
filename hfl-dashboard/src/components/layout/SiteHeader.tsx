"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { Menu, X } from "lucide-react";
import { NAV, SITE } from "@/content/site";
import { MotionPreferenceControl } from "@/components/motion/MotionPreference";
import { PublicContentSearch } from "@/components/content/PublicContentSearch";

function normalise(path: string): string {
  return path.endsWith("/") ? path : `${path}/`;
}

export function isActive(pathname: string, item: (typeof NAV)[number]): boolean {
  const p = normalise(pathname);
  const matches: readonly string[] = "match" in item ? item.match : [item.href];
  return matches.some((m) => p === m || p.startsWith(m));
}

export function SiteHeader() {
  const pathname = usePathname() ?? "/";
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header
      className={`sticky top-0 z-40 transition-[background-color,box-shadow,backdrop-filter] duration-200 ${
        scrolled || open ? "glass !rounded-none !border-x-0 !border-t-0" : "bg-transparent"
      }`}
    >
      <a href="#main" className="sr-only-focusable absolute left-4 top-3 z-50 rounded-md bg-accent px-3 py-2 font-medium text-white">
        Skip to content
      </a>
      <div className="container-site flex h-[72px] items-center gap-4">
        <Link href="/" className="group flex shrink-0 items-center gap-3" aria-label={`${SITE.wordmark} ${SITE.descriptor}, home`}>
          <span aria-hidden className="brand-orb" />
          <span className="font-display text-[1.3rem] leading-none text-ink">{SITE.wordmark}</span>
          <span className="hidden text-sm font-medium text-subtle 2xl:inline">{SITE.descriptor}</span>
        </Link>

        <nav aria-label="Primary" className="ml-auto hidden lg:block">
          <ul className="flex items-center gap-1">
            {NAV.map((item) => {
              const active = isActive(pathname, item);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`relative inline-flex min-h-10 items-center gap-1.5 rounded-full px-3.5 text-[0.85rem] font-semibold transition-all ${
                      active ? "bg-bg-elevated text-accent shadow-[var(--clay-inset-sm)]" : "text-muted hover:text-accent"
                    }`}
                  >
                    {"caution" in item && <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-caution" />}
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="ml-auto flex items-center gap-2 lg:ml-2">
          <PublicContentSearch />
          <div className="hidden md:block">
            <MotionPreferenceControl compact />
          </div>
          <Link href="/architecture/" className="btn btn-primary btn-sm hidden sm:inline-flex">
            Explore the system
          </Link>
          <button
            ref={buttonRef}
            type="button"
            className="btn btn-ghost btn-sm lg:hidden"
            aria-expanded={open}
            aria-controls={menuId}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X size={18} aria-hidden /> : <Menu size={18} aria-hidden />}
          </button>
        </div>
      </div>

      <div id={menuId} hidden={!open} className="border-t border-line bg-bg-elevated/95 lg:hidden">
        <nav aria-label="Mobile" className="container-site py-4">
          <ul className="grid gap-1">
            {NAV.map((item) => {
              const active = isActive(pathname, item);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`flex min-h-12 items-center gap-2 rounded-lg px-3 text-base ${
                      active ? "bg-surface-raised text-ink" : "text-muted"
                    }`}
                  >
                    {"caution" in item && <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-caution" />}
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/architecture/" className="btn btn-primary btn-sm">
              Explore the system
            </Link>
            <MotionPreferenceControl compact={false} />
          </div>
        </nav>
      </div>
    </header>
  );
}
