import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Макроаналитика",
  description: "Макроэкономическая аналитика для России и мировых рынков",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
