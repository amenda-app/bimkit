export const config = {
  port: parseInt(process.env.PORT || "4000", 10),
  bimServiceUrl: process.env.BIM_SERVICE_URL || "http://localhost:8000",
};
