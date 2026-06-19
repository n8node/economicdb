import { ProductSidebar } from "./ProductSidebar";
import { ProductTopbar } from "./ProductTopbar";

export function ProductShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app">
      <ProductSidebar />
      <div className="main">
        <ProductTopbar />
        {children}
      </div>
    </div>
  );
}
