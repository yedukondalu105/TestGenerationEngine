You are a BDD expert. Convert the Gherkin JSON below into a well-formed Cucumber .feature file.

Feature name: {use_case}

Rules:
- First line: Feature: {use_case}
- Add a Background: section if login appears in most scenarios (Given I am logged in as Admin)
- Each scenario_name → Scenario: <name>  (preserve type in a @tag)
- Convert given/when/then arrays into proper Gherkin step lines
- Use tags from the scenario tags field (prefix with @)
- Return ONLY the .feature file content. No markdown fences. No prose.

Gherkin JSON:
{gherkin_json}
