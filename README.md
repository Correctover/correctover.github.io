<p align="center">
  <strong>[ CCS Compliance Status: ⚠️ NON_COMPLIANT ]</strong>
</p>

<h1 align="center">Correctover</h1>

<p align="center">
  <strong>The Industry Standard for LLM Output Verification</strong>
</p>

<p align="center">
  <em>Don't guess if your agent is hallucinating. Verify it against the Cryptographic Compliance Standard (CCS).</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/correctover/"><img src="https://img.shields.io/pypi/v/correctover" alt="PyPI"></a>
  <a href="https://www.npmjs.com/package/correctover"><img src="https://img.shields.io/npm/v/correctover" alt="npm"></a>
  <a href="https://doi.org/10.5281/zenodo.21234580"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21234580-blue" alt="DOI"></a>
</p>

---

## Why Correctover?

Modern agent frameworks (AutoGen, LangGraph, CrewAI) focus on *orchestration*. **We focus on truth.**

Correctover provides the protocol layer for **LLM Output Verification**, ensuring that what your model outputs meets the deterministic requirements of production-grade systems.

The mathematical invariant: **Required(τ) ⊆ Supported(τ)**

---

## 30-Second Compliance Audit

Run the CCS Scanner to see how your infrastructure ranks:

```bash
pip install correctover

# Run a full compliance scan across all dimensions
python -m correctover.scan --all

# Scan a specific provider
python -m correctover.scan --provider openai

# Generate compliance report
python -m correctover.scan --report
```

**Latest scan results — 20,299 real production responses:**

| Provider | Model | Score | Certification |
|----------|-------|-------|---------------|
| Meta | Llama-3.1-70B | 70% | ⚠️ CONDITIONAL |
| OpenAI | GPT-OSS-120B | 35% | ❌ NON-COMPLIANT |
| Microsoft | Phi-3.5-MoE | 0% | 💀 BROKEN |
| Microsoft | Phi-4-Multimodal | 0% | 💀 BROKEN |
| Databricks | DBRX | 0% | 💀 BROKEN |
| IBM | Granite-34B | 0% | 💀 BROKEN |
| Google | Gemma-3-12B | 0% | 💀 BROKEN |

### 0 of 7 certified. 85.7% cannot be used in production.

---

## CCS Certification Levels

We certify infrastructures based on our 20,299-record production dataset across 5 verification dimensions.

| Level | Criteria | Meaning |
|-------|----------|---------|
| ✅ **CERTIFIED** | ≥95% across all 5 dimensions | Production-ready. Output integrity verified. |
| ⚠️ **CONDITIONAL** | 70-95%, core schema valid | Functional but has architectural limitations in edge cases. |
| ❌ **NON-COMPLIANT** | <70%, schema violations | Fails boundary verification. Not safe for production agents. |
| 💀 **BROKEN** | 0%, fundamental failures | Persistent infrastructure-level failures. Endpoint non-functional. |

### The 5 Verification Dimensions

| Dimension | What It Tests |
|-----------|---------------|
| **D1 — Schema** | Does the output match the required structure? |
| **D2 — Arithmetic** | Does 2+3=5? Silent corruption detection. |
| **D3 — Factual** | Are references real or hallucinated? |
| **D4 — Temporal** | Is the model time-aware? Stale knowledge detection. |
| **D5 — Reproducibility** | Same input → same output? Non-determinism boundary. |

---

## Integration

```python
from correctover import CCSValidator

validator = CCSValidator(
    required_fields=["result", "action", "timestamp"],
    forbidden_fields=["error", "stack_trace"],
    enable_integrity=True
)

result = validator.validate(llm_output, trace_id="agent-001")

if not result.is_valid:
    raise IntegrityViolation(result.errors)
```

---

## The 5 Components

| Component | Function |
|-----------|----------|
| **CCS-Core** | Schema validation engine. Required/Supported/Forbidden fields. |
| **CCS-Compliance** | Regulatory mapping. HIPAA, GDPR, SOC2. |
| **CCS-Cost-Flow** | Token budget enforcement. Prevents cost overruns. |
| **CCS-Integrity** | HMAC-based output binding. Cryptographic proof. |
| **CCS-Audit** | Immutable audit trails. Full provenance chain. |

---

## Join the Integrity Movement

We are publishing the **Q3 Industry Reliability Benchmark on July 11, 2026**.

Frameworks that have not adopted CCS verification protocols will be categorized by their technical risk level.

Full responsible disclosure: [correctover.github.io/disclosures](https://correctover.github.io/disclosures/20260707-llm-verification-failures)

---

## Resources

- **CCS Specification:** [github.com/Correctover/standards](https://github.com/Correctover/standards)
- **Benchmark Methodology:** [BENCHMARK-METHODOLOGY.md](https://github.com/Correctover/standards/blob/main/BENCHMARK-METHODOLOGY.md)
- **CCS Scanner:** [demo/ccs_scanner.py](https://github.com/Correctover/correctover.github.io/blob/main/demo/ccs_scanner.py)
- **PyPI:** [pypi.org/project/correctover](https://pypi.org/project/correctover/)
- **npm:** [npmjs.com/package/correctover](https://www.npmjs.com/package/correctover)
- **DOI:** [10.5281/zenodo.21234580](https://zenodo.org/records/21234580)

---

<p align="center">
  <a href="https://github.com/Correctover/standards"><strong>Documentation & Full Audit Methodology</strong></a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="mailto:wangguigui@correctover.com"><strong>Get Your Compliance Badge</strong></a>
</p>

---

<p align="center">
  <em>Correctover doesn't failover. Correctover verifies.</em>
</p>
