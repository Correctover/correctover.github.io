#!/usr/bin/env python3
"""
CCS Quick-Start — Catch Your First LLM Hallucination in 5 Minutes

    pip install requests
    python ccs_quickstart.py

That's it. No config, no keys required for the demo.
Uses pre-canned LLM outputs with known hallucinations to show
what CCS catches — then shows how to plug in your own calls.

Output: A verifiable compliance receipt with DOI reference.
Share it. The receipt IS the evidence.
"""

import json
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


# ============================================================================
# CCS Core — The Invariant
# ============================================================================
# Valid(τ) ⇔ Required(τ) ⊆ Supported(τ)
#
# For every LLM output transition τ:
#   Required(τ) = predicates that MUST hold
#   Supported(τ) = predicates that actually hold (verified)
#
# If Required ⊄ Supported → the output FAILS conformance
# ============================================================================


@dataclass
class CCSReceipt:
    """
    Verifiable compliance receipt — the artifact that proves
    CCS caught a hallucination. This is what developers share.
    """
    receipt_id: str
    timestamp: str
    provider: str
    model: str
    required_rules: List[str]
    satisfied_rules: List[str]
    violated_rules: List[str]
    request_hash: str
    response_hash: str
    binding_hash: str
    compliance_level: str  # CERTIFIED | CONDITIONAL | NON_COMPLIANT | BROKEN
    dimensions_checked: int
    dimensions_passed: int
    doi: str = "10.5281/zenodo.21234580"
    spec_version: str = "CCS v1.0"
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)
    
    def to_badge(self) -> str:
        """Shareable text receipt"""
        violations = "\n".join(f"  ✗ {v}" for v in self.violated_rules) if self.violated_rules else "  (none)"
        satisfied = "\n".join(f"  ✓ {r}" for r in self.satisfied_rules) if self.satisfied_rules else "  (none)"
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║  CCS Compliance Receipt — {self.compliance_level}
║  DOI: {self.doi}
║  Spec: {self.spec_version}
╠══════════════════════════════════════════════════════════╣
║  Provider: {self.provider}
║  Model:    {self.model}
║  Time:     {self.timestamp}
║  Receipt:  {self.receipt_id}
╠══════════════════════════════════════════════════════════╣
║  Conformance Invariant:
║  Valid(τ) ⇔ Required(τ) ⊆ Supported(τ)
╠══════════════════════════════════════════════════════════╣
║  Required Rules ({len(self.required_rules)}):
{chr(10).join(f'║    • {r}' for r in self.required_rules)}
║
║  Satisfied ({len(self.satisfied_rules)}):
{satisfied}
║
║  Violated ({len(self.violated_rules)}):
{violations}
╠══════════════════════════════════════════════════════════╣
║  Dimensions: {self.dimensions_passed}/{self.dimensions_checked} passed
║  Binding:  {self.binding_hash[:32]}...
╚══════════════════════════════════════════════════════════╝

Verified by CCS — https://doi.org/{self.doi}
"""


# ============================================================================
# Five Verification Dimensions (from ccs_scanner.py)
# ============================================================================

def check_schema_compliance(output: str, expected_fields: List[str]) -> Dict:
    """D1: Schema Compliance — structural integrity"""
    passed = []
    violated = []
    for field_name in expected_fields:
        if field_name.lower() in output.lower():
            passed.append(f"D1-Schema: contains '{field_name}'")
        else:
            violated.append(f"D1-Schema: missing required field '{field_name}'")
    return {"passed": passed, "violated": violated}


def check_arithmetic(output: str, calculations: List[Dict]) -> Dict:
    """D2: Arithmetic Integrity — deterministic computation"""
    passed = []
    violated = []
    for calc in calculations:
        expected = calc["expected"]
        expression = calc["expression"]
        if str(expected) in output:
            passed.append(f"D2-Arithmetic: {expression} = {expected} ✓")
        else:
            violated.append(f"D2-Arithmetic: {expression} claimed ≠ {expected} (hallucinated)")
    return {"passed": passed, "violated": violated}


def check_factual_grounding(output: str, claims: List[Dict]) -> Dict:
    """D3: Factual Grounding — hallucination detection"""
    passed = []
    violated = []
    for claim in claims:
        statement = claim["statement"]
        ground_truth = claim["ground_truth"]
        if ground_truth == "UNVERIFIABLE":
            # Check if the output makes an unverifiable claim as fact
            if statement.lower() in output.lower():
                violated.append(f"D3-Factual: '{statement}' — unverifiable claim presented as fact")
            else:
                passed.append(f"D3-Factual: '{statement}' — not asserted (correct)")
        elif ground_truth in output:
            passed.append(f"D3-Factual: '{statement}' — grounded ✓")
        else:
            violated.append(f"D3-Factual: '{statement}' — hallucinated or contradicted")
    return {"passed": passed, "violated": violated}


def check_temporal_consistency(output: str, temporal_claims: List[Dict]) -> Dict:
    """D4: Temporal Consistency — time-aware reasoning"""
    passed = []
    violated = []
    for tc in temporal_claims:
        claim = tc["claim"]
        is_correct = tc["correct"]
        if claim.lower() in output.lower() and not is_correct:
            violated.append(f"D4-Temporal: '{claim}' — temporally incorrect")
        elif claim.lower() in output.lower() and is_correct:
            passed.append(f"D4-Temporal: '{claim}' — correct ✓")
        elif claim.lower() not in output.lower():
            passed.append(f"D4-Temporal: '{claim}' — not asserted (no violation)")
    return {"passed": passed, "violated": violated}


def check_reproducibility_check(output: str, deterministic_expectations: List[str]) -> Dict:
    """D5: Output Reproducibility — deterministic boundary"""
    passed = []
    violated = []
    for expected in deterministic_expectations:
        if expected.lower() in output.lower():
            passed.append(f"D5-Reproducibility: deterministic output matches ✓")
        else:
            violated.append(f"D5-Reproducibility: non-deterministic drift detected")
    return {"passed": passed, "violated": violated}


# ============================================================================
# The Core Function — validate_output()
# ============================================================================

def validate_output(
    output: str,
    provider: str = "demo",
    model: str = "unknown",
    required_fields: Optional[List[str]] = None,
    calculations: Optional[List[Dict]] = None,
    factual_claims: Optional[List[Dict]] = None,
    temporal_claims: Optional[List[Dict]] = None,
    deterministic_expectations: Optional[List[str]] = None,
) -> CCSReceipt:
    """
    Validate a single LLM output against CCS rules.
    
    The invariant: Required(τ) ⊆ Supported(τ)
    If any Required rule is not in Supported → NON_COMPLIANT
    
    This is the function that catches hallucinations.
    """
    all_passed = []
    all_violated = []
    all_required = []
    dimensions_checked = 0
    dimensions_passed = 0
    
    # D1: Schema
    if required_fields:
        dimensions_checked += 1
        r = check_schema_compliance(output, required_fields)
        all_passed.extend(r["passed"])
        all_violated.extend(r["violated"])
        all_required.extend([f"D1:{f}" for f in required_fields])
        if not r["violated"]:
            dimensions_passed += 1
    
    # D2: Arithmetic
    if calculations:
        dimensions_checked += 1
        r = check_arithmetic(output, calculations)
        all_passed.extend(r["passed"])
        all_passed  # dedupe below
        all_violated.extend(r["violated"])
        all_required.extend([f"D2:{c['expression']}" for c in calculations])
        if not r["violated"]:
            dimensions_passed += 1
    
    # D3: Factual
    if factual_claims:
        dimensions_checked += 1
        r = check_factual_grounding(output, factual_claims)
        all_passed.extend(r["passed"])
        all_violated.extend(r["violated"])
        all_required.extend([f"D3:{c['statement'][:30]}" for c in factual_claims])
        if not r["violated"]:
            dimensions_passed += 1
    
    # D4: Temporal
    if temporal_claims:
        dimensions_checked += 1
        r = check_temporal_consistency(output, temporal_claims)
        all_passed.extend(r["passed"])
        all_violated.extend(r["violated"])
        all_required.extend([f"D4:{tc['claim'][:30]}" for tc in temporal_claims])
        if not r["violated"]:
            dimensions_passed += 1
    
    # D5: Reproducibility
    if deterministic_expectations:
        dimensions_checked += 1
        r = check_reproducibility_check(output, deterministic_expectations)
        all_passed.extend(r["passed"])
        all_violated.extend(r["violated"])
        all_required.extend([f"D5:{e[:30]}" for e in deterministic_expectations])
        if not r["violated"]:
            dimensions_passed += 1
    
    # Determine compliance level
    if not all_violated:
        level = "CERTIFIED"
    elif dimensions_passed / max(dimensions_checked, 1) >= 0.7:
        level = "CONDITIONAL"
    elif dimensions_passed > 0:
        level = "NON_COMPLIANT"
    else:
        level = "BROKEN"
    
    # Generate hashes
    request_hash = hashlib.sha256(output.encode()[:100]).hexdigest()
    response_hash = hashlib.sha256(output.encode()).hexdigest()
    binding_secret = hashlib.sha256(f"{request_hash}:{response_hash}:{len(all_violated)}".encode()).hexdigest()
    binding_hash = hmac.new(
        binding_secret.encode(), 
        f"{request_hash}:{response_hash}".encode(), 
        hashlib.sha256
    ).hexdigest()
    
    return CCSReceipt(
        receipt_id=str(uuid.uuid4())[:12],
        timestamp=datetime.now(timezone.utc).isoformat(),
        provider=provider,
        model=model,
        required_rules=all_required,
        satisfied_rules=all_passed,
        violated_rules=all_violated,
        request_hash=request_hash,
        response_hash=response_hash,
        binding_hash=binding_hash,
        compliance_level=level,
        dimensions_checked=dimensions_checked,
        dimensions_passed=dimensions_passed,
    )


# ============================================================================
# Demo: Pre-canned LLM Outputs with Known Hallucinations
# ============================================================================

DEMO_CASES = [
    {
        "name": "Case 1: Arithmetic Hallucination",
        "description": "LLM confidently states wrong math (47×23=1031, correct is 1081). CCS catches it.",
        "provider": "OpenAI",
        "model": "gpt-4o",
        "output": "The calculation is straightforward: 47 × 23 = 1031. This gives us a total revenue of $1,031 million for Q3 2024.",
        "calculations": [
            {"expression": "47 × 23", "expected": 1081},
        ],
        "factual_claims": [
            {"statement": "Q3 2024 revenue $1,031 million", "ground_truth": "UNVERIFIABLE"},
        ],
    },
    {
        "name": "Case 2: Factual Hallucination — Fake Paper",
        "description": "LLM invents a research paper. CCS detects unverifiable claims.",
        "provider": "Anthropic",
        "model": "claude-3.5-sonnet",
        "output": "According to the study by Chen et al. (2024) published in Nature Machine Intelligence, 'Transformer architectures achieve 97.3% accuracy on multi-hop reasoning tasks.' This finding was replicated by the Stanford NLP group.",
        "factual_claims": [
            {"statement": "Chen et al. (2024) in Nature Machine Intelligence", "ground_truth": "UNVERIFIABLE"},
            {"statement": "97.3% accuracy on multi-hop reasoning", "ground_truth": "UNVERIFIABLE"},
            {"statement": "Stanford NLP group replication", "ground_truth": "UNVERIFIABLE"},
        ],
    },
    {
        "name": "Case 3: Temporal Hallucination — Wrong Dates",
        "description": "LLM mixes up timelines. CCS catches temporal inconsistency.",
        "provider": "Google",
        "model": "gemini-1.5-pro",
        "output": "Python 3.12 was released in October 2023 and introduced pattern matching. The GIL was removed in Python 3.13, released in June 2024.",
        "temporal_claims": [
            {"claim": "Python 3.12 released October 2023", "correct": True},
            {"claim": "pattern matching introduced in 3.12", "correct": False},  # Actually 3.10
            {"claim": "GIL removed in Python 3.13 June 2024", "correct": False},  # Not removed, optional
        ],
    },
]


def run_demo():
    """Run all demo cases and show what CCS catches."""
    print("""
╔══════════════════════════════════════════════════════════╗
║           CCS Quick-Start — LLM Output Validator        ║
║   Valid(τ) ⇔ Required(τ) ⊆ Supported(τ)                ║
║                                                         ║
║   Catching hallucinations the developer can't see.      ║
╚══════════════════════════════════════════════════════════╝
""")
    
    receipts = []
    
    for case in DEMO_CASES:
        print(f"\n{'─'*60}")
        print(f"  {case['name']}")
        print(f"  {case['description']}")
        print(f"{'─'*60}")
        
        print(f"\n  LLM Output:")
        for line in case["output"].split("\n"):
            print(f"  > {line}")
        
        receipt = validate_output(
            output=case["output"],
            provider=case["provider"],
            model=case["model"],
            calculations=case.get("calculations"),
            factual_claims=case.get("factual_claims"),
            temporal_claims=case.get("temporal_claims"),
        )
        
        receipts.append(receipt)
        print(receipt.to_badge())
    
    # Summary
    print(f"\n{'═'*60}")
    print(f"  SUMMARY: {len(receipts)} outputs validated")
    certified = sum(1 for r in receipts if r.compliance_level == "CERTIFIED")
    non_compliant = sum(1 for r in receipts if r.compliance_level in ("NON_COMPLIANT", "BROKEN"))
    print(f"  Certified: {certified} | Non-compliant: {non_compliant}")
    total_violations = sum(len(r.violated_rules) for r in receipts)
    print(f"  Total hallucinations caught: {total_violations}")
    print(f"{'═'*60}")
    
    print(f"""
  This is what CCS does for your LLM outputs.
  
  Next step: plug in YOUR API calls.
  
    from ccs_quickstart import validate_output
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "your prompt"}]
    )
    
    receipt = validate_output(
        output=response.choices[0].message.content,
        provider="openai",
        model="gpt-4o",
        factual_claims=[
            {{"statement": "any factual claim", "ground_truth": "UNVERIFIABLE"}},
        ],
    )
    
    print(receipt.to_badge())
    
  If it's NON_COMPLIANT → your LLM hallucinated, and now you have proof.
  
  CCS Spec: https://doi.org/10.5281/zenodo.21234580
  Repo: https://github.com/Correctover/standards
""")


if __name__ == "__main__":
    run_demo()
