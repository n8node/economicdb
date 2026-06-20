import { FREQ_LABELS, type IndicatorListItem } from "./indicators";

const CATEGORY_HINTS: Record<string, string> = {
  fx: "Валютный курс: соотношение двух валют. Показывает, сколько единиц одной валюты нужно за единицу другой.",
  inflation: "Индикатор изменения цен. Отражает темп роста потребительских или производственных цен в экономике.",
  rates: "Процентная ставка, доходность или стоимость заимствований. Ключевой сигнал монетарной политики и финансовых условий.",
  labor: "Показатель рынка труда: занятость, безработица или спрос на рабочую силу.",
  industrial: "Динамика промышленного производства и загрузки мощностей. Индикатор деловой активности в секторе.",
  equities: "Динамика фондового индекса или рыночной стоимости акций. Отражает настроение инвесторов.",
  consumption: "Потребительский спрос и розничные продажи. Показывает активность домохозяйств.",
  construction: "Строительная активность: разрешения, продажи жилья или объёмы работ.",
  income: "Доходы населения или располагаемый доход. Важен для оценки покупательной способности.",
  financial: "Финансовые условия и стресс на рынках. Сводный индикатор доступности кредита и риска.",
  credit: "Объём или темп роста кредитования. Показывает, насколько активно банки финансируют экономику.",
  gdp: "Валовой внутренний продукт или его рост. Главный показатель масштаба и динамики экономики.",
  commodities: "Цена или котировка сырьевого актива. Важен для торгового баланса и инфляционных ожиданий.",
  external: "Внешний сектор: резервы, торговля или платёжный баланс.",
  employment: "Занятость и безработица. Отражает состояние рынка труда.",
  industry: "Промышленное производство и деловая активность в обрабатывающих отраслях.",
};

function fxDescription(name: string): string | null {
  const pair = name.match(/^([A-Z]{3})\s*\/\s*([A-Z]{3})$/i);
  if (!pair) return null;
  const [, base, quote] = pair;
  return `Курс ${base.toUpperCase()} к ${quote.toUpperCase()}: сколько единиц ${quote.toUpperCase()} стоит одна единица ${base.toUpperCase()}.`;
}

export function buildIndicatorDescription(
  item: Pick<IndicatorListItem, "category" | "unit" | "frequency" | "name_ru" | "country">,
  categoryLabel?: string,
): string {
  if (item.category === "fx") {
    const fxHint = fxDescription(item.name_ru);
    if (fxHint) return fxHint;
  }

  const hint = CATEGORY_HINTS[item.category];
  if (hint) return hint;

  const label = categoryLabel || item.category;
  const freq = FREQ_LABELS[item.frequency] || item.frequency;
  const unit = item.unit ? ` Единица измерения: ${item.unit}.` : "";
  return `Макроэкономический показатель категории «${label}». Обновляется с частотой ${freq}.${unit}`;
}
