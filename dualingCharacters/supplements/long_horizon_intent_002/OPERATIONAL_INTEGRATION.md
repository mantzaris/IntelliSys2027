# Operational integration, separate from scientific freezes

The original core controller and frozen review_001 coordinator retain ownership.
No waiter was replaced and no GPU worker was launched. The existing review
coordinator eventually invokes the older optional unseen-profile controller.
An explicit priority guard in that **unfrozen operational controller** now checks
`artifacts/optional_priority.json` before doing any GPU work. Pending intent_002
causes a clean deferred return; it does not schedule intent inference.

Priority is required core → review_001 → intent_002 → older optional unseen profiles.
At this session's deadline, unexecuted intent_002 remains disabled. A subsequent
continuation must explicitly authorize a new session before updating its deadline
or resolving its optional priority. No background extension is left waiting to
spend GPU time after this session. The existing core and review campaign continue
under their previously authorized controls.

The CPU reporting helpers accept explicit `PCC_REPORT_OUTPUT` and
`PCC_REPORT_CACHE` paths, routed by `operations.py`. Their default historical
paths are unchanged. Completed audit caches are reused, and new reports are
written here rather than overwriting the overnight handoff. This changes only
report destinations, not a scientific estimator, input, checkpoint or GPU setting.
