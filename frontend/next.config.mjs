/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  reactStrictMode: true,
  // Mismo origen en producción; relativo evita problemas de CORS.
  images: { unoptimized: true },
};

export default nextConfig;
