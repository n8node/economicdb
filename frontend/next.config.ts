import type { NextConfig } from "next";

const noStoreHeaders = [
  { key: "Cache-Control", value: "no-store, no-cache, must-revalidate, max-age=0" },
  { key: "Pragma", value: "no-cache" },
  { key: "Expires", value: "0" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    return [
      { source: "/app", headers: noStoreHeaders },
      { source: "/app/:path*", headers: noStoreHeaders },
      { source: "/adminus", headers: noStoreHeaders },
      { source: "/adminus/:path*", headers: noStoreHeaders },
    ];
  },
};

export default nextConfig;
