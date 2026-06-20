import { SOURCE_LABELS } from "@/lib/indicators";

type MetaTagsProps = {
  country: string;
  source: string;
  countryLabel?: string;
  sourceLabel?: string;
  className?: string;
};

export function MetaTags({ country, source, countryLabel, sourceLabel, className }: MetaTagsProps) {
  return (
    <div className={className ? `meta-tags ${className}` : "meta-tags"}>
      <span className="country-flag">{countryLabel || country.toUpperCase()}</span>
      <span className={`source-tag ${source}`}>{sourceLabel || SOURCE_LABELS[source] || source}</span>
    </div>
  );
}
