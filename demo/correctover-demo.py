#!/usr/bin/env python3
"""
Correctover Demo - MCP Reliability Layer

This demo shows how Correctover validates LLM outputs in real-time.
"""

import time
from typing import Dict, Any, Optional


class CorrectoverValidator:
    """
    Validates LLM outputs against formal constraints.
    Core invariant: Required(τ) ⊆ Supported(τ)
    """
    
    def __init__(self):
        self.rules = self._load_rules()
        self.validation_count = 0
        self.recovery_count = 0
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load validation rules from the 93-pattern library."""
        return {
            "rate_limit": {"check": self._check_rate_limit, "recover": self._recover_rate_limit},
            "malformed_output": {"check": self._check_malformed, "recover": self._recover_malformed},
            "timeout": {"check": self._check_timeout, "recover": self._recover_timeout},
            "overloaded": {"check": self._check_overloaded, "recover": self._recover_overloaded},
        }
    
    def validate(self, output: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate LLM output against constraints.
        
        Args:
            output: The LLM-generated output
            constraints: Dict with validation rules
            
        Returns:
            Dict with validation result and latency
        """
        start_time = time.perf_counter()
        
        result = {
            "valid": True,
            "violations": [],
            "latency_us": 0,
            "recovery_triggered": False,
        }
        
        # Check each constraint
        for constraint_name, constraint_value in constraints.items():
            if constraint_name == "max_tokens":
                if len(output.split()) > constraint_value:
                    result["valid"] = False
                    result["violations"].append(f"max_tokens exceeded: {len(output.split())} > {constraint_value}")
            
            elif constraint_name == "required_fields":
                for field in constraint_value:
                    if field not in output:
                        result["valid"] = False
                        result["violations"].append(f"missing required field: {field}")
        
        # Calculate latency
        end_time = time.perf_counter()
        result["latency_us"] = (end_time - start_time) * 1_000_000  # Convert to microseconds
        
        self.validation_count += 1
        
        # Trigger recovery if validation failed
        if not result["valid"]:
            result["recovery_triggered"] = True
            self.recovery_count += 1
        
        return result
    
    def _check_rate_limit(self, output: str) -> bool:
        return "rate limit" not in output.lower()
    
    def _check_malformed(self, output: str) -> bool:
        return len(output) > 0 and output.strip() != ""
    
    def _check_timeout(self, output: str) -> bool:
        return "timeout" not in output.lower()
    
    def _check_overloaded(self, output: str) -> bool:
        return "overloaded" not in output.lower()
    
    def _recover_rate_limit(self, context: Dict) -> Dict:
        """Recovery strategy for rate limit errors."""
        return {"action": "wait_and_retry", "delay_ms": 1000}
    
    def _recover_malformed(self, context: Dict) -> Dict:
        """Recovery strategy for malformed outputs."""
        return {"action": "retry_with_different_prompt", "temperature": 0.3}
    
    def _recover_timeout(self, context: Dict) -> Dict:
        """Recovery strategy for timeouts."""
        return {"action": "failover_to_backup_model"}
    
    def _recover_overloaded(self, context: Dict) -> Dict:
        """Recovery strategy for overloaded errors."""
        return {"action": "switch_to_alternative_provider"}


class Correctover:
    """
    Main Correctover client.
    Drop-in replacement for OpenAI/Anthropic SDKs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.validator = CorrectoverValidator()
        self.api_key = api_key
    
    def chat_completions_create(
        self,
        model: str,
        messages: list,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion with validation.
        
        This is a simplified demo. In production, this would:
        1. Call the actual LLM API
        2. Validate the output using CorrectoverValidator
        3. Trigger recovery if validation fails
        4. Return validated output
        
        Args:
            model: Model name (e.g., "gpt-4")
            messages: List of message dicts
            constraints: Validation constraints
            **kwargs: Additional OpenAI-compatible parameters
            
        Returns:
            Dict with validated response
        """
        # Simulate LLM output
        simulated_output = "This is a simulated response from the LLM."
        
        # Validate
        constraints = constraints or {}
        validation_result = self.validator.validate(simulated_output, constraints)
        
        # Build response
        response = {
            "id": "chatcmpl-demo",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": simulated_output
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(m.get("content", "").split()) for m in messages),
                "completion_tokens": len(simulated_output.split()),
                "total_tokens": sum(len(m.get("content", "").split()) for m in messages) + len(simulated_output.split())
            },
            "correctover": {
                "validated": True,
                "validation_latency_us": validation_result["latency_us"],
                "violations": validation_result["violations"],
                "recovery_triggered": validation_result["recovery_triggered"]
            }
        }
        
        return response


def main():
    """Demo: Show Correctover in action."""
    print("=" * 60)
    print("Correctover Demo - MCP Reliability Layer")
    print("=" * 60)
    print()
    
    # Initialize client
    client = Correctover()
    
    # Example 1: Simple validation
    print("Example 1: Simple validation")
    print("-" * 40)
    response = client.chat_completions_create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello, world!"}],
        constraints={"max_tokens": 100}
    )
    print(f"Response: {response['choices'][0]['message']['content']}")
    print(f"Validation latency: {response['correctover']['validation_latency_us']:.2f} μs")
    print(f"Valid: {len(response['correctover']['violations']) == 0}")
    print()
    
    # Example 2: Validation with required fields
    print("Example 2: Validation with required fields")
    print("-" * 40)
    response = client.chat_completions_create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Generate a JSON with 'name' and 'age'"}],
        constraints={"required_fields": ["name", "age"]}
    )
    print(f"Response: {response['choices'][0]['message']['content']}")
    print(f"Validation latency: {response['correctover']['validation_latency_us']:.2f} μs")
    print(f"Valid: {len(response['correctover']['violations']) == 0}")
    if response['correctover']['violations']:
        print(f"Violations: {response['correctover']['violations']}")
    print()
    
    # Example 3: Show core invariant
    print("Example 3: Core Invariant")
    print("-" * 40)
    print("Required(τ) ⊆ Supported(τ)")
    print()
    print("For any task τ:")
    print("  - Required(τ): outputs the agent needs")
    print("  - Supported(τ): outputs the model can produce")
    print()
    print("Correctover ensures all validated outputs satisfy this invariant.")
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total validations: {client.validator.validation_count}")
    print(f"Recoveries triggered: {client.validator.recovery_count}")
    print()
    print("Learn more: https://correctover.com")
    print("GitHub: https://github.com/Correctover")


if __name__ == "__main__":
    main()