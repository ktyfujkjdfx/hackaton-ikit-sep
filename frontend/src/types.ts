// Зеркало docs/CONTRACT.md, разделы 5-6. Фронт ничего не считает — только эти типы.

export type Income = {
  id: string
  name: string
  amount: number
  date: string
  confirmed: boolean
}

export type Obligation = {
  id: string
  name: string
  amount: number
  date: string
}

export type Spend = {
  id: string
  name: string
  amount: number
  date: string
  category: string
}

export type Goal = {
  name: string
  target: number
  current: number
  date: string
}

export type Category = {
  name: string
  per_day: number
}

export type HistoryOp = {
  date: string
  name: string
  amount: number
  category: string
}

export type Situation = {
  today: string
  balance: number
  daily: number
  incomes: Income[]
  obligations: Obligation[]
  spends: Spend[]
  goal: Goal | null
  categories: Category[] | null
  history: HistoryOp[]
}

export type Purchase = {
  amount: number
  date: string
  name: string
}

export type ValidationError = {
  field: 'balance' | 'daily' | 'incomes' | 'obligations' | 'goal' | 'purchase'
  index: number | null
  subfield: 'amount' | 'date' | null
  message: string
}

export type SeriesStats = {
  min: number
  min_date: string
  first_negative_date: string | null
  last_negative_date: string | null
  max_deficit: number
  first_negative_amount: number
}

export type DaySeries = {
  days: { date: string; balance: number }[]
  stats: SeriesStats
}

export type Headline = {
  state: 'ok' | 'tight' | 'deficit' | 'depends' | 'no_income'
  next_income: { name: string; date: string; days: number; confirmed: boolean } | null
  next_confirmed_income: { name: string; date: string; days: number; confirmed: boolean } | null
  min_balance: number
  min_date: string
  first_negative_date: string | null
  max_deficit: number
  days_of_spending_left: number
}

export type EventKind = 'income' | 'obligation' | 'spend' | 'purchase'

export type Event = {
  date: string
  kind: EventKind
  name: string
  amount: number
  confirmed: boolean | null
}

export type MoneyTypesBlock<T> = { total: number; items: T[] }

export type MoneyTypes = {
  stable_income: MoneyTypesBlock<Income>
  unstable_income: MoneyTypesBlock<Income>
  stable_expenses: MoneyTypesBlock<Obligation>
  variable_expenses: { total: number; daily: number; days: number; one_off: Spend[] }
  reliable_total: number
}

export type Ease = 'easy' | 'hard'

export type ReduceOption =
  | { kind: 'postpone'; date: string; ease: Ease }
  | {
      kind: 'reduce'
      per_day: number
      new_daily: number
      until: string
      days: number
      possible: boolean
      ease: Ease
      flexible_per_day: number
    }
  | {
      kind: 'earn'
      amount: number
      by_date: string
      first_amount: number
      first_date: string
      ease: Ease
    }

export type DeficitPlan = {
  deficit: number
  by_date: string
  first_needed_amount: number
  first_needed_date: string
  based_on: 'base' | 'pessimistic' | 'purchase'
  options: ReduceOption[]
}

export type GoalPlan = {
  monthly_surplus: number
  per_day: number
  remaining: number
  eta: string | null
  late_days: number | null
  need_monthly: number | null
  eta_with_purchase: string | null
  shift_days: number | null
}

export type PurchaseCheck = {
  purchase: Purchase
  verdict: 'ok' | 'tight' | 'deficit'
  before: SeriesStats
  after: SeriesStats
  earliest_safe_date: string | null
  safe_depends_on_unconfirmed: boolean
  goal: GoalPlan | null
  plan: DeficitPlan | null
}

export type HistoryItem = HistoryOp & { regular: boolean; large: boolean }

export type Dashboard = {
  today: string
  horizon_days: number
  headline: Headline
  scenarios: {
    base: DaySeries
    pessimistic: DaySeries | null
    with_purchase: DaySeries | null
    with_purchase_pessimistic: DaySeries | null
  }
  events: Event[]
  money_types: MoneyTypes
  goal: GoalPlan | null
  purchase: PurchaseCheck | null
  deficit_plan: DeficitPlan | null
  history: HistoryItem[]
  show_learn_card: boolean
  assumptions: string[]
  unknowns: string[]
}

export type ChecksResult = {
  passed: number
  total: number
  items: { id: number; title: string; expected: string; got: string; ok: boolean }[]
}

export type ChatRole = 'user' | 'assistant'

export type ChatRequest = {
  situation: Situation
  purchase: Purchase | null
  message: string
  history: { role: ChatRole; text: string }[]
}

export type ChatIntent =
  | 'purchase_check'
  | 'forecast'
  | 'explain'
  | 'deficit_plan'
  | 'categories'
  | 'term'
  | 'add_entry'
  | 'invest_info'
  | 'refusal'
  | 'clarify'
  | 'off_topic'

export type ChatTone = 'good' | 'bad' | 'neutral'

export type ChatFact = { label: string; value: string; tone: ChatTone | null }

export type ChatAction = {
  kind:
    | 'open_explain'
    | 'defer'
    | 'show_jobs'
    | 'save_entry'
    | 'open_learn'
    | 'check_purchase'
    | 'open_add_income'
  label: string
  payload: Record<string, unknown>
}

export type ProposedEntry = {
  type: 'spend' | 'income'
  name: string
  amount: number
  date: string
  confirmed: boolean
  category: string
}

export type ChatResponse = {
  intent: ChatIntent
  tool_calls: { name: string; args: Record<string, unknown> }[]
  headline: string
  tone: ChatTone
  facts: ChatFact[]
  text: string
  source: { title: string; url: string } | null
  purchase: Purchase | null
  proposed_entry: ProposedEntry | null
  actions: ChatAction[]
  nlu: { mode: 'onnx' | 'sklearn' | 'rules'; label: string; confidence: number }
  explainer: 'templates' | 'yandex' | 'anthropic'
  guarded: boolean
}

export type Persona = {
  id: string
  title: string
  subtitle: string
}

export type PersonaDetail = {
  id: string
  who: string
  situation: Situation
}
