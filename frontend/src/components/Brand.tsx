import { BRAND_NAME } from '../lib/brand'

// Логотип: жёлтый скруглённый квадрат с чёрным компасом. Рисуем вектором, а не картинкой,
// чтобы он остался чётким на любом экране и не тянул лишний запрос.
export function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 48 48" role="img" aria-label={`Логотип «${BRAND_NAME}»`}>
      <rect width="48" height="48" rx="11" fill="#FFDD2D" />
      <g fill="#2A2A2A">
        <path d="M24 6.6A17.4 17.4 0 1 0 24 41.4 17.4 17.4 0 0 0 24 6.6Zm0 2.9a14.5 14.5 0 1 1 0 29 14.5 14.5 0 0 1 0-29Z" />
        <path d="M21.4 8.1h5.2L24 13.6ZM21.4 39.9h5.2L24 34.4ZM8.1 21.4v5.2L13.6 24ZM39.9 21.4v5.2L34.4 24Z" />
        <path d="m35.9 12.1-7.9 15.8-15.8 7.9 7.9-15.8Z" />
      </g>
      <circle cx="24" cy="24" r="3" fill="#FFDD2D" />
    </svg>
  )
}

export function Brand() {
  return (
    <div className="brand">
      <BrandMark />
      {BRAND_NAME}
    </div>
  )
}
