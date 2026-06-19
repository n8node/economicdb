function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="content">
      <div className="page-head">
        <h1>{title}</h1>
      </div>
      <div className="card card-pad">
        <p>Экран в разработке.</p>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  return <PlaceholderPage title="Алерты" />;
}
