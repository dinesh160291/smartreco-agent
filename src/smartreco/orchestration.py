"""Agent-framework wrapper — Google ADK binding of the 13-node workflow.

The graph contract (named nodes, typed state, explicit edges, bounded loops,
per-node tracing — core 21) lives in smartreco.pipeline.WORKFLOW_GRAPH; this
module only supplies the framework. Every stage delegates to its owning engine;
model calls route through the AI Provider Gateway inside the stages — never
through the framework's own model layer. Swapping to LangGraph (the documented
fallback) would replace only this module (stack-decisions.md).
"""

import asyncio
import contextvars
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import InMemoryRunner
from google.genai import types

from smartreco.pipeline import WORKFLOW_GRAPH, WorkflowContext

# The stages need live handles (db session, chroma client, gateway) that must
# not round-trip through the framework's serializable session state — they are
# carried per-invocation via a context variable instead.
_CURRENT: contextvars.ContextVar[tuple[WorkflowContext, dict]] = contextvars.ContextVar(
    "smartreco_workflow_ctx")

_STAGE_FNS = dict(WORKFLOW_GRAPH)


_HALTED = "_halted"


class StageAgent(BaseAgent):
    """One deterministic (or Tier-classified) workflow node as an ADK agent.
    Delegates to the stage function; emits one trace event."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        workflow_ctx, state = _CURRENT.get()
        # The halt is enforced here, in state we own, and only *then* signalled
        # to the framework. Setting `end_invocation` alone was a request this
        # version of SequentialAgent does not honour between sub-agents: the
        # node after `resolve_journey` ran anyway and died on the journey_id it
        # had just been told did not exist, so a routine SKIP surfaced as a
        # FAILED run. The graph contract is core 21's, not the framework's —
        # a wrapper that can only ask politely is not binding it.
        if state.get(_HALTED):
            yield Event(author=self.name, invocation_id=ctx.invocation_id)
            return
        proceed = _STAGE_FNS[self.name](workflow_ctx, state)
        if not proceed:
            state[_HALTED] = True
            ctx.end_invocation = True  # halt the sequential chain (no work)
        yield Event(author=self.name, invocation_id=ctx.invocation_id)


def build_workflow_agent() -> SequentialAgent:
    return SequentialAgent(
        name="smartreco_workflow",
        sub_agents=[StageAgent(name=name) for name, _fn in WORKFLOW_GRAPH],
    )


def adk_executor(ctx: WorkflowContext, state: dict) -> None:
    """Executor for pipeline.run_workflow: runs the stage graph through the
    ADK runner. Same stages, same state, framework-supplied sequencing."""

    async def _run() -> None:
        runner = InMemoryRunner(agent=build_workflow_agent(), app_name="smartreco")
        session = await runner.session_service.create_session(
            app_name="smartreco", user_id=str(ctx.user_id))
        token = _CURRENT.set((ctx, state))
        try:
            async for _event in runner.run_async(
                user_id=str(ctx.user_id), session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text="run")]),
            ):
                pass
        finally:
            _CURRENT.reset(token)

    asyncio.run(_run())
