import Link from "next/link";
import type { DashboardOverview } from "@/lib/dashboard";

const COUNTRY_LABELS: Record<string, string> = {
  ru: "RU",
  eu: "EU",
  us: "US",
};

export function DashboardEventsCard({ events }: { events: DashboardOverview["calendar_events"] }) {
  return (
    <div className="card card-pad dashboard-side-card">
      <div className="dashboard-card-head">
        <div className="dashboard-card-title-wrap">
          <i className="ti ti-calendar-event dashboard-card-icon" />
          <h3 className="card-title">События недели</h3>
        </div>
        <Link href="/app/calendar" target="_top" className="dashboard-card-link">
          Календарь <i className="ti ti-chevron-right" />
        </Link>
      </div>

      <div className="dashboard-event-list">
        {events.map((event) => (
          <div key={`${event.title}-${event.date_label}`} className="dashboard-event-row">
            <div className="dashboard-event-date">{event.date_label}</div>
            <div className="dashboard-event-main">
              <p className="dashboard-event-title">
                <span className={`dashboard-event-dot ${event.importance}`} aria-hidden />
                {event.title}
                <span className={`dashboard-event-country ${event.country}`}>
                  {COUNTRY_LABELS[event.country] || event.country.toUpperCase()}
                </span>
              </p>
              {event.subtext ? <p className="dashboard-event-sub">{event.subtext}</p> : null}
            </div>
            <div className="dashboard-event-time">{event.time_label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
