/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow env vars prefixed with NEXT_PUBLIC_ to be available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;