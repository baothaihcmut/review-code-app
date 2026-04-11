import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',

  // nên tắt để build nhẹ hơn
  reactCompiler: false,
};

export default nextConfig;