export function ChatPlaceholder() {
  return (
    <section
      aria-label="HR assistant placeholder"
      className="flex min-h-88 flex-col rounded-2xl border border-zinc-200 bg-white shadow-sm"
    >
      <header className="border-b border-zinc-100 px-5 py-4">
        <h2 className="text-base font-semibold text-zinc-900">HR assistant</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Chat is not connected yet. Retrieval and generation will be added later.
        </p>
      </header>

      <div className="flex flex-1 items-center justify-center px-6 py-10 text-center">
        <p className="max-w-sm text-sm leading-6 text-zinc-500">
          Employees will ask HR questions here. Answers will come from internal
          documents, with citations and region-specific filtering, once RAG is
          implemented.
        </p>
      </div>

      <div className="flex gap-2 border-t border-zinc-100 p-4">
        <input
          type="text"
          disabled
          placeholder="Ask a question about leave, benefits, or policy…"
          className="flex-1 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-500"
        />
        <button
          type="button"
          disabled
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white opacity-50"
        >
          Send
        </button>
      </div>
    </section>
  );
}
