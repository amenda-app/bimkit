import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DCAB BIM Report Studio",
  description: "BIM-Datenextraktion und Berichterstellung",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
