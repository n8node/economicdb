import Link from "next/link";
import type { DashboardOverview } from "@/lib/dashboard";

const COUNTRY_LABELS: Record<string, string> = {
  ru: "RU",
  eu: "EU",
  us: "US",
};

function parseDateLabel(label: string): { day: string; month: string } {
  const [day, month] = label.split(/\s+/);
  return { day: day ?? label, month: month ?? "" };
}

export function DashboardEventsCard({ events }: { events: DashboardOverview["calendar_events"] }) {
  return (
    <div className="card card-pad dashboard-side-card dashboard-events-card">
      <div className="dashboard-events-head">
        <div className="dashboard-card-title-wrap">
          <span className="dashboard-events-icon-box" aria-hidden>
            <i className="ti ti-calendar-event" />
          </span>
          <h3 className="card-title">События недели</h3>
        </div>
        <Link href="/app/calendar" target="_top" className="dashboard-events-link">
          Календарь <i className="ti ti-chevron-right" />
        </Link>
      </div>

      <div className="dashboard-event-list">
        {events.map((event) => {
          const { day, month } = parseDateLabel(event.date_label);
          return (
            <div key={`${event.title}-${event.date_label}`} className="dashboard-event-row">
              <div className="dashboard-event-date">
                <span className="dashboard-event-day">{day}</span>
                {month ? <span className="dashboard-event-month">{month}</span> : null}
              </div>
              <div className="dashboard-event-main">
                <p className="dashboard-event-title">
                  <span className={`dashboard-event-dot ${event.importance}`} aria-hidden />
                  <span className="dashboard-event-name">{event.title}</span>
                  <span className="dashboard-event-country">
                    {COUNTRY_LABELS[event.country] || event.country.toUpperCase()}
                  </span>
                </p>
                {event.subtext ? <p className="dashboard-event-sub">{event.subtext}</p> : null}
              </div>
              <div className="dashboard-event-time">{event.time_label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
