import "@/styles/admin.css";
import { AdminShell } from "@/components/admin/AdminShell";

export default function AdminProtectedLayout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
