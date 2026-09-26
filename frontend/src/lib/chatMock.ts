import type { ChatResponse } from '../types'

// Пока /api/chat роли B не готов — собираем ChatResponse руками для каждой
// кнопки AskPanel, чтобы форма ответа 1-в-1 совпадала с docs/CONTRACT.md
// (раздел 6) уже сейчас, без расхождений на потом.
export function buildChatResponse(overrides: Partial<ChatResponse>): ChatResponse {
  return {
    intent: 'clarify',
    tool_calls: [],
    headline: '',
    tone: 'neutral',
    facts: [],
    text: '',
    source: null,
    purchase: null,
    proposed_entry: null,
    actions: [],
    nlu: { mode: 'rules', label: 'clarify', confidence: 1 },
    explainer: 'templates',
    guarded: false,
    ...overrides,
  }
}
