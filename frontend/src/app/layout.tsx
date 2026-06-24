import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "@tabler/icons-webfont/tabler-icons.min.css";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Макроаналитика",
  description: "Макроэкономическая аналитика для России и мировых рынков",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const deployId = process.env.NEXT_PUBLIC_BUILD_ID ?? "dev";

  return (
    <html lang="ru" className={`${inter.variable} ${jetbrains.variable}`}>
      <head>
        <meta name="deploy-id" content={deployId} />
        <script src="/macro-hard-navigation.js" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
