import express from "express";
import cors from "cors";
import { createProxyMiddleware } from "http-proxy-middleware";
import { config } from "./config.js";

const app = express();

app.use(cors());
app.use(express.json());

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "backend" });
});

// Proxy all /bim/* requests to the BIM service
app.use(
  "/bim",
  createProxyMiddleware({
    target: config.bimServiceUrl,
    changeOrigin: true,
    pathRewrite: { "^/bim": "/bim" },
  })
);

app.listen(config.port, () => {
  console.log(`Backend listening on port ${config.port}`);
  console.log(`BIM service proxy → ${config.bimServiceUrl}`);
});
