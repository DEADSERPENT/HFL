import type { NextConfig } from "next";
import path from "node:path";

/**
 * Static export: the Observatory is a plain set of HTML/CSS/JS files with no
 * server, no API routes and no runtime connection to any research system.
 */
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  reactStrictMode: true,
  poweredByHeader: false,
  productionBrowserSourceMaps: false,
  images: { unoptimized: true },
  turbopack: { root: path.resolve(__dirname) },
};

export default nextConfig;
