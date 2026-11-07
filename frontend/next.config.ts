import type { NextConfig } from "next";

const mode = process.env.NEXT_PUBLIC_REKNYX_MODE || 'preview';
if (!['preview', 'api'].includes(mode)) throw new Error('NEXT_PUBLIC_REKNYX_MODE must be preview or api');
let upstream = '';
if (mode === 'api') {
  const url = new URL(process.env.REKNYX_BACKEND_ORIGIN || '');
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('REKNYX_BACKEND_ORIGIN must be a fixed HTTP(S) origin');
  upstream = url.origin;
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() { return mode === 'api' ? [{source: '/api/v1/:path*', destination: `${upstream}/api/v1/:path*`}] : []; },
};

export default nextConfig;
