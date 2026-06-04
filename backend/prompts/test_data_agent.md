You are extracting test data from Gherkin test scenarios for a data-driven test suite.

Suite: {use_case}

Analyze the Gherkin scenarios below and extract ALL concrete test data values used in them.
Return a flat JSON object where keys are descriptive names and values are the exact strings used.

Common keys for authentication suites:
  valid_username, valid_password       — credentials that succeed
  invalid_username, invalid_password   — credentials that fail
  empty_value                          — "" (empty string, for empty-field tests)
  short_username, short_password       — values below minimum length
  invalid_format                       — value with invalid characters (e.g. "!nv@l!d")
  max_length_username, max_length_password — value at/above maximum allowed length

For other suites, extract keys matching the actual data in the scenarios
(e.g. employee_name, department_name, job_title, start_date, end_date, amount, etc.).

Rules:
- Return ONLY a flat JSON object — no nesting, no arrays
- All values must be strings
- If a value is repeated in multiple scenarios use it once under the most descriptive key
- Do NOT invent values that are not in the scenarios; derive them from the scenario text
- Return ONLY valid JSON. No markdown fences. No prose.

Gherkin scenarios:
{gherkin_json}
