"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type UserItem = {
  id: number;
  email: string;
  email_verified: boolean;
  personal_data_accepted_at: string;
  created_at: string;
};

type UsersResponse = {
  items: UserItem[];
  total: number;
};

const PAGE_SIZE = 50;

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function UsersPanel() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [selected, setSelected] = useState<UserItem | null>(null);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const page = useMemo(() => Math.floor(offset / PAGE_SIZE) + 1, [offset]);
  const pages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  async function load(nextOffset = offset, nextQuery = query) {
    setLoading(true);
    setMessage("");
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(nextOffset),
      });
      const search = nextQuery.trim();
      if (search) params.set("q", search);

      const data = await adminAuthFetch<UsersResponse>(`/admin/users?${params.toString()}`);
      setUsers(data.items);
      setTotal(data.total);
      setOffset(nextOffset);
      setSelected((current) => {
        if (!current) return data.items[0] || null;
        return data.items.find((item) => item.id === current.id) || data.items[0] || null;
      });
    } catch {
      setMessage("Не удалось загрузить пользователей");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(0).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function searchUsers(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await load(0, query);
  }

  async function deleteUser(user: UserItem) {
    const confirmed = window.confirm(`Удалить пользователя ${user.email}? Это действие нельзя отменить.`);
    if (!confirmed) return;

    setDeletingId(user.id);
    setMessage("");
    try {
      await adminAuthFetch(`/admin/users/${user.id}`, { method: "DELETE" });
      setMessage(`Пользователь ${user.email} удалён`);
      const nextOffset = users.length === 1 && offset > 0 ? Math.max(0, offset - PAGE_SIZE) : offset;
      await load(nextOffset, query);
    } catch {
      setMessage("Не удалось удалить пользователя");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="admin-page-head">
        <div>
          <h1 style={{ marginTop: 0 }}>Пользователи</h1>
          <p className="muted" style={{ maxWidth: 760 }}>
            Список пользователей продукта: регистрационные данные, статус email и согласие на обработку персональных данных.
          </p>
        </div>
        <div className="admin-users-total">
          <span className="muted">Всего</span>
          <strong>{total}</strong>
        </div>
      </div>

      <form className="admin-users-toolbar" onSubmit={searchUsers}>
        <input
          className="admin-input"
          type="search"
          placeholder="Поиск по email или ID"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" className="admin-btn primary" disabled={loading}>
          Найти
        </button>
        <button
          type="button"
          className="admin-btn"
          disabled={loading || (!query && offset === 0)}
          onClick={() => {
            setQuery("");
            void load(0, "");
          }}
        >
          Сбросить
        </button>
      </form>

      {message ? <p className="muted">{message}</p> : null}

      <div className="admin-users-layout">
        <div className="admin-table-scroll">
          <table className="admin-table admin-users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Статус email</th>
                <th>Согласие ПДн</th>
                <th>Создан</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr
                  key={user.id}
                  className={selected?.id === user.id ? "selected" : ""}
                  onClick={() => setSelected(user)}
                >
                  <td>{user.id}</td>
                  <td>
                    <button type="button" className="admin-link-button" onClick={() => setSelected(user)}>
                      {user.email}
                    </button>
                  </td>
                  <td>{user.email_verified ? "Подтверждён" : "Не подтверждён"}</td>
                  <td>{formatDate(user.personal_data_accepted_at)}</td>
                  <td>{formatDate(user.created_at)}</td>
                  <td>
                    <button
                      type="button"
                      className="admin-btn danger"
                      disabled={deletingId === user.id}
                      onClick={(event) => {
                        event.stopPropagation();
                        void deleteUser(user);
                      }}
                    >
                      {deletingId === user.id ? "Удаление…" : "Удалить"}
                    </button>
                  </td>
                </tr>
              ))}
              {!users.length ? (
                <tr>
                  <td colSpan={6} className="muted">
                    {loading ? "Загрузка…" : "Пользователи не найдены"}
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <aside className="admin-panel admin-user-detail">
          <h2>Карточка пользователя</h2>
          {selected ? (
            <div className="admin-detail-list">
              <div>
                <span className="muted">ID</span>
                <strong>{selected.id}</strong>
              </div>
              <div>
                <span className="muted">Email</span>
                <strong>{selected.email}</strong>
              </div>
              <div>
                <span className="muted">Email подтверждён</span>
                <strong>{selected.email_verified ? "Да" : "Нет"}</strong>
              </div>
              <div>
                <span className="muted">Согласие на ПДн</span>
                <strong>{formatDate(selected.personal_data_accepted_at)}</strong>
              </div>
              <div>
                <span className="muted">Дата регистрации</span>
                <strong>{formatDate(selected.created_at)}</strong>
              </div>
              <button
                type="button"
                className="admin-btn danger"
                disabled={deletingId === selected.id}
                onClick={() => void deleteUser(selected)}
              >
                {deletingId === selected.id ? "Удаление…" : "Удалить пользователя"}
              </button>
            </div>
          ) : (
            <p className="muted">Выберите пользователя в таблице.</p>
          )}
        </aside>
      </div>

      <div className="admin-users-pagination">
        <button
          type="button"
          className="admin-btn"
          disabled={loading || offset === 0}
          onClick={() => void load(Math.max(0, offset - PAGE_SIZE), query)}
        >
          Назад
        </button>
        <span className="muted">
          Страница {page} из {pages}
        </span>
        <button
          type="button"
          className="admin-btn"
          disabled={loading || offset + PAGE_SIZE >= total}
          onClick={() => void load(offset + PAGE_SIZE, query)}
        >
          Вперёд
        </button>
      </div>
    </div>
  );
}
