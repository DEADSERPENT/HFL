"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";
import { useMotion } from "@/components/motion/MotionPreference";

// The first page load renders without an entrance animation, so content is
// visible immediately; later client navigations get a short fade.
let navigated = false;

export default function Template({ children }: { children: React.ReactNode }) {
  const { reduced } = useMotion();
  const animate = navigated && !reduced;
  useEffect(() => {
    navigated = true;
  }, []);
  return (
    <motion.div initial={animate ? { opacity: 0, y: 6 } : false} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22, ease: "easeOut" }}>
      {children}
    </motion.div>
  );
}
