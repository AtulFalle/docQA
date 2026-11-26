from typing import Any, cast

import structlog
from temporalio.testing import ActivityEnvironment
from temporalio.worker import ActivityInboundInterceptor, ExecuteActivityInput

from docqa_workers.log_context import LogContextInterceptor


class _CaptureContext(ActivityInboundInterceptor):
    def __init__(self) -> None:  # no next interceptor: this is the innermost one
        pass

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:  # noqa: A002
        return structlog.contextvars.get_contextvars()


async def _run() -> dict[str, Any]:
    wrapped = LogContextInterceptor().intercept_activity(_CaptureContext())
    result: dict[str, Any] = await wrapped.execute_activity(cast(ExecuteActivityInput, None))
    return result


async def test_activity_logs_carry_workflow_ids() -> None:
    env = ActivityEnvironment()
    ctx = await env.run(_run)
    assert ctx["workflow_id"] == env.info.workflow_id
    assert ctx["workflow_run_id"] == env.info.workflow_run_id
    assert ctx["activity"] == env.info.activity_type
    assert ctx["attempt"] == env.info.attempt
    assert structlog.contextvars.get_contextvars() == {}
