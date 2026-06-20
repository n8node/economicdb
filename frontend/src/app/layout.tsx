import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { NavigationFallback } from "@/components/NavigationFallback";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

const hardNavigationScript = `
(function () {
  function shouldHandle(anchor, event) {
    if (!anchor || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (anchor.target && anchor.target !== "_self") return false;
    if (anchor.hasAttribute("download")) return false;
    var url = new URL(anchor.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    return url.pathname === "/app" || url.pathname.indexOf("/app/") === 0 || url.pathname.indexOf("/adminus") === 0;
  }

  function handleClick(event) {
    var target = event.target;
    if (!target || !target.closest) return;
    var anchor = target.closest("a[href]");
    if (!shouldHandle(anchor, event)) return;
    event.preventDefault();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    window.location.assign(anchor.href);
  }

  window.__macroHardNavigation = true;
  window.addEventListener("click", handleClick, true);
  document.addEventListener("click", handleClick, true);
})();
`;

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
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/2.47.0/iconfont/tabler-icons.min.css"
        />
      </head>
      <body>
        <script id="macro-hard-navigation" dangerouslySetInnerHTML={{ __html: hardNavigationScript }} />
        <NavigationFallback />
        {children}
      </body>
    </html>
  );
}
