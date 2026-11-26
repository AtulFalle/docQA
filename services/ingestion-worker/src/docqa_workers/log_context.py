"""Temporal interceptor that adds workflow and activity IDs to every activity log line."""

from typing import Any

from temporalio import activity
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    Interceptor,
)

from docqa_core.logging import log_context


class LogContextInterceptor(Interceptor):
    """Bind ``workflow_id``, ``workflow_run_id``, ``activity`` and ``attempt`` for activities."""

    def intercept_activity(self, next: ActivityInboundInterceptor) -> ActivityInboundInterceptor:  # noqa: A002 - Temporal's parameter name
        """Wrap each activity execution."""
        return _ActivityLogContext(next)


class _ActivityLogContext(ActivityInboundInterceptor):
    async def execute_activity(self, input: ExecuteActivityInput) -> Any:  # noqa: A002 - Temporal's signature
        info = activity.info()
        with log_context(
            workflow_id=info.workflow_id,
            workflow_run_id=info.workflow_run_id,
            activity=info.activity_type,
            attempt=info.attempt,
        ):
            return await super().execute_activity(input)
