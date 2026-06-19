function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="content">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p className="meta">{description}</p>
        </div>
      </div>
      <div className="card card-pad">
        <p>Экран в разработке — UI переносится из макетов `design/mockups/`.</p>
      </div>
    </div>
  );
}

export default function IndicatorsPage() {
  return <PlaceholderPage title="Показатели" description="Каталог макроэкономических показателей" />;
}
