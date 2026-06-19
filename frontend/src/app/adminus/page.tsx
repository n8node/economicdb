import "@/styles/admin.css";
import { AdminLoginForm } from "@/components/admin/AdminLoginForm";

export default function AdminLoginPage() {
  return (
    <main className="admin-page">
      <div className="admin-card">
        <h1>Админ-панель</h1>
        <p className="muted">Вход для super_admin · economicdb.com/adminus</p>
        <AdminLoginForm />
      </div>
    </main>
  );
}
