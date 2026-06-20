import { SOURCE_LABELS } from "@/lib/indicators";

type MetaTagsProps = {
  country: string;
  source: string;
  countryLabel?: string;
  sourceLabel?: string;
  className?: string;
  compact?: boolean;
};

export function MetaTags({
  country,
  source,
  countryLabel,
  sourceLabel,
  className,
  compact = false,
}: MetaTagsProps) {
  const rootClass = [
    "meta-tags",
    compact ? "meta-tags-compact" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <span className="country-flag">{countryLabel || country.toUpperCase()}</span>
      <span className={`source-tag ${source}`}>{sourceLabel || SOURCE_LABELS[source] || source}</span>
    </div>
  );
}

export function SourceTag({ source, label }: { source: string; label?: string }) {
  return <span className={`source-tag ${source}`}>{label || SOURCE_LABELS[source] || source}</span>;
}
