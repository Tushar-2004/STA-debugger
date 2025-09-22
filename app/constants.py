PROMPT_TEMPLATE = """
You are a GenAI-powered timing violation debugger for semiconductor design.
You will receive one STA path at a time in JSON format.

### Input Path JSON:
{path_json}

### INSTRUCTION:
1. If status = "VIOLATED":
   * Identify the root cause based on path_type, slack, and logic_chain
   * Provide detailed technical explanation
   * Suggest 3 specific, actionable fixes with priority levels
2. If status = "MET":
   * Provide a brief confirmation that timing is met

### OUTPUT FORMAT:
Return ONLY valid JSON with these keys:
- "startpoint", "endpoint", "path_type", "status", "slack"
- "root_cause": string (detailed technical explanation)
- "severity": "critical", "high", "medium", "low"
- "suggestions": list of objects with "fix", "priority", "explanation"
- "estimated_effort": "low", "medium", "high"

### EXAMPLE OUTPUT FOR VIOLATION:
{{
  "startpoint": "U1/Q",
  "endpoint": "U5/D", 
  "path_type": "max",
  "status": "VIOLATED",
  "slack": -0.85,
  "root_cause": "Combinational path delay exceeds clock period due to multiple levels of logic and high fanout",
  "severity": "high",
  "suggestions": [
    {{
      "fix": "Insert pipeline register",
      "priority": "high",
      "explanation": "Break the long combinational path into two clock cycles"
    }},
    {{
      "fix": "Use faster cell library",
      "priority": "medium", 
      "explanation": "Replace standard cells with high-speed variants"
    }}
  ],
  "estimated_effort": "medium"
}}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "startpoint": "reg1/Q",
            "endpoint": "reg2/D",
            "slack": -1.2,
            "path_type": "setup",
            "logic_chain": ["AND2X1", "OR2X1", "XOR2X1"]
        },
        "output": {
            "root_cause": "3-level combinational logic exceeds timing budget",
            "severity": "critical",
            "suggestions": [
                {"fix": "Logic restructuring", "priority": "high", "explanation": "Reduce logic levels"},
                {"fix": "Pipeline insertion", "priority": "high", "explanation": "Add intermediate register"}
            ]
        }
    }
]