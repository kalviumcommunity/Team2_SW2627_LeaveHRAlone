import { ApiStatus } from "@/components/ApiStatus";
import { ChatPlaceholder } from "@/components/ChatPlaceholder";

export default function Home() {
  return (
    <div className="min-h-full bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <p className="text-sm font-semibold tracking-tight text-zinc-900">
            LeaveHRAlone
          </p>
          <ApiStatus />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Internal HR assistant
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight text-zinc-900">
          LeaveHRAlone
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
          An AI-powered assistant that will answer employee questions from your
          team&apos;s HR documents, including leave policies, benefits, and
          region-specific handbooks. The retrieval system is not built yet; this
          page is the starting foundation.
        </p>

        <div className="mt-10">
          <ChatPlaceholder />
        </div>
      </main>
    </div>
  );
}
