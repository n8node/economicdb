import "@/styles/product.css";
import { ProductShell } from "@/components/layout/ProductShell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <ProductShell>{children}</ProductShell>;
}
