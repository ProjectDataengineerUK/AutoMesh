# HITL stale precondition

When approved state differs from current state, reject the application with `STALE_PRECONDITION`. Do not apply or silently rebase the action. Notify the approver with current state and create a new decision request if the action remains appropriate.
