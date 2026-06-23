import "@/styles/product.css";
import { ProductAuthGate } from "@/components/auth/ProductAuthGate";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <ProductAuthGate>{children}</ProductAuthGate>;
}
