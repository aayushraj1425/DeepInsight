export default {
  cacheDir: ".vite-runtime",
  optimizeDeps: {
    include: ["react", "react-dom/client", "react/jsx-dev-runtime"],
  },
}
