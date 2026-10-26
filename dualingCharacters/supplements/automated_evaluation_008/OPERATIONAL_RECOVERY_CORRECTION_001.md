# Preserve and classify the supervisor error

The original exact-ID preparer correctly refused to proceed because the supervisor replaced the worker-specific exception in status.json with “Preserved incomplete stage008 run.” The original status and preparer are unchanged. No model call occurred in that preparation failure.

`continuation_v2.py` instead requires a separately recorded classification: the exact timeout exception in the retained log, the immutable failed-status hash, the original worker absent, and the GPU empty. It retains the same immutable-ID selection and freezes the continuation before launch. The correction concerns operational fault provenance, not prompts, sample allocation, model labels, or scientific endpoints.
