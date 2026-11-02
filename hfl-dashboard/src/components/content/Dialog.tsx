"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { useMotion } from "@/components/motion/MotionPreference";

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea, input:not([disabled]), select, [tabindex]:not([tabindex="-1"])';

/**
 * Modal dialog / drawer: traps focus, closes on Escape or backdrop click, and
 * returns focus to the element that opened it.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  variant = "drawer",
  initialFocus,
}: {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  variant?: "drawer" | "center";
  initialFocus?: React.RefObject<HTMLElement | null>;
}) {
  const panel = useRef<HTMLDivElement>(null);
  const returnTo = useRef<HTMLElement | null>(null);
  const titleId = useId();
  const descId = useId();
  const { reduced } = useMotion();

  useEffect(() => {
    if (!open) return;
    returnTo.current = document.activeElement as HTMLElement | null;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const t = window.setTimeout(() => {
      const target = initialFocus?.current ?? panel.current?.querySelector<HTMLElement>(FOCUSABLE) ?? panel.current;
      target?.focus();
    }, 0);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panel.current) return;
      const items = Array.from(panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((el) => !el.hasAttribute("hidden"));
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const first = items[0]!;
      const last = items[items.length - 1]!;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      const r = returnTo.current;
      if (r && document.contains(r)) r.focus();
    };
  }, [open, onClose, initialFocus]);

  if (typeof document === "undefined") return null;

  const isDrawer = variant === "drawer";
  const panelAnim = reduced
    ? { initial: { opacity: 1 }, animate: { opacity: 1 }, exit: { opacity: 1 } }
    : isDrawer
      ? { initial: { opacity: 0, x: 28 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: 28 } }
      : { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 10 } };

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[60]">
          <motion.div
            className="absolute inset-0 bg-[rgba(37,31,24,0.28)] backdrop-blur-[3px]"
            initial={{ opacity: reduced ? 1 : 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: reduced ? 1 : 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            aria-hidden
          />
          <motion.div
            ref={panel}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={description ? descId : undefined}
            tabIndex={-1}
            {...panelAnim}
            transition={{ duration: reduced ? 0 : 0.22, ease: [0.2, 0.7, 0.2, 1] }}
            className={
              isDrawer
                ? "absolute inset-y-0 right-0 flex w-full max-w-xl flex-col border-l border-line bg-bg-elevated shadow-soft outline-none"
                : "absolute left-1/2 top-[8vh] flex max-h-[84vh] w-[min(92vw,640px)] -translate-x-1/2 flex-col rounded-[var(--radius-lg)] border border-line bg-bg-elevated shadow-soft outline-none"
            }
          >
            <div className="flex items-start gap-4 border-b border-line px-6 py-5">
              <div className="min-w-0 flex-1">
                <h2 id={titleId} className="font-display text-2xl text-ink">
                  {title}
                </h2>
                {description && (
                  <div id={descId} className="mt-1 text-sm text-muted">
                    {description}
                  </div>
                )}
              </div>
              <button type="button" onClick={onClose} className="btn btn-ghost btn-sm" aria-label="Close">
                <X size={16} aria-hidden />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
