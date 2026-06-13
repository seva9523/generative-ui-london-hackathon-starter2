"use client";

import { useState } from "react";
import { z } from "zod";
import {
  CopilotChat,
  useAgent,
  useRenderTool,
} from "@copilotkit/react-core/v2";
import { SiteNav } from "@/components/pdf-analyst/Brand";
import { SurfaceCanvas, CanvasEmptyState } from "@/components/pdf-analyst/SurfaceCanvas";
import { FilteredUserMessage } from "@/components/pdf-analyst/FilteredUserMessage";
import { FilteredAssistantMessage } from "@/components/pdf-analyst/FilteredAssistantMessage";
import { Split } from "@/components/pdf-analyst/Split";
import { extractPdfText } from "@/lib/pdf";

const AGENT_ID = "fixed_agent";

export default function FixedPage() {
  const { agent: _agent } = useAgent({ agentId: AGENT_ID });
  const [loaded, setLoaded] = useState<{
    filename: string;
    pages: number;
    chars: number;
  } | null>(null);

  // render_dashboard returns A2UI operations for the canvas. Register the
  // tool so CopilotKit does not render it as an unknown chat message while
  // the surface bus paints the dashboard on the right.
  useRenderTool({
    name: "render_dashboard",
    parameters: z.any(),
    render: ({ status }) => {
      if (status === "complete") return <></>;
      return (
        <div className="surface-soft px-3 py-2 my-1 flex items-center gap-3 text-[13px] text-[var(--ink-2)]">
          <span className="relative inline-flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--mint)] opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[var(--mint)]" />
          </span>
          <span>Rendering investment dashboard…</span>
        </div>
      );
    },
  });

  return (
    <div className="h-screen flex flex-col bg-[var(--bg)]">
      <SiteNav active="fixed" />

      <div className="flex-1 min-h-0 flex">
      <Split
        persistKey="fixed.split"
        initialLeftFraction={0.32}
        left={
          <div className="h-full flex flex-col copilot-chat-wrapper">
            {loaded && (
              <div className="shrink-0 px-4 py-2 border-b border-[var(--line)] flex items-center gap-2 bg-[color-mix(in_oklab,var(--mint)_8%,var(--surface))]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0d6b4f]" />
                <span className="mono text-[10.5px] uppercase tracking-[0.12em] text-[var(--ink)]">
                  loaded
                </span>
                <span className="text-[12.5px] font-medium text-[var(--ink)] truncate">
                  {loaded.filename}
                </span>
                <span className="text-[11px] text-[var(--ink)] ml-auto">
                  {loaded.pages} pg · {Math.round(loaded.chars / 1000)}k chars
                </span>
              </div>
            )}
            <div className="flex-1 min-h-0">
              <CopilotChat
                agentId={AGENT_ID}
                chatView={{
                  messageView: {
                    userMessage: FilteredUserMessage,
                    assistantMessage: FilteredAssistantMessage,
                  },
                }}
                attachments={{
                  enabled: true,
                  accept: "application/pdf",
                  maxSize: 20 * 1024 * 1024,
                  onUpload: async (file) => {
                    const { text, pages } = await extractPdfText(file);
                    setLoaded({
                      filename: file.name,
                      pages,
                      chars: text.length,
                    });
                    return {
                      type: "data",
                      value: text.slice(0, 60_000),
                      mimeType: "text/plain",
                      metadata: {
                        filename: file.name,
                        pages,
                        originalMime: "application/pdf",
                      },
                    };
                  },
                  onUploadFailed: (err) =>
                    console.warn("[pdf upload failed]", err),
                }}
                labels={{
                  chatInputPlaceholder:
                    "Attach a pitch deck (📎), then ask for an IC dashboard…",
                  welcomeMessageText:
                    "Attach a startup pitch deck, then ask: “Create an investment committee dashboard.”",
                }}
              />
            </div>
          </div>
        }
        right={
          <SurfaceCanvas
            channel={AGENT_ID}
            emptyState={
              <CanvasEmptyState
                title="Investment canvas is empty"
                subtitle="Attach a startup pitch deck in the chat (📎) and ask FundLens AI to create the investment committee dashboard."
                hint={
                  <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--ink)]">
                    try: “Create an investment committee memo.”
                  </span>
                }
              />
            }
          />
        }
      />
      </div>
    </div>
  );
}
