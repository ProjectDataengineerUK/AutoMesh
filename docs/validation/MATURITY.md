# Capability maturity

- **Not Validated:** required code evidence is absent, stale, skipped, or failed.
- **Implemented:** unit, contract, and lint gates pass for the current commit.
- **Locally Validated:** implemented plus local integration evidence.
- **Infrastructure Validated:** local validation plus current external smoke evidence.
- **Operationally Complete:** infrastructure validation plus recovery, alert, and runbook evidence.

External PASS evidence expires. A skip is always visible and never promotes maturity.
