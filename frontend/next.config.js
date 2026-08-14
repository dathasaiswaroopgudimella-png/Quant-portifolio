/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Note: NEXT_PUBLIC_API_URL is intentionally omitted here so client-side code
  // dynamically auto-detects localhost:8000 in dev and relative /api/v1 in production.
}

module.exports = nextConfig
