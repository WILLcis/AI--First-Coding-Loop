import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class AutoMergePolicyTest(unittest.TestCase):
    def test_policy_document_exists(self) -> None:
        text = (ROOT / "docs/AUTO_MERGE_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("CI passing should not be treated as a human approval gate.", text)
        self.assertIn("Required Merge Gates", text)
        self.assertIn("Stop And Ask", text)

    def test_main_instructions_authorize_auto_merge_after_gates(self) -> None:
        text = (ROOT / "AGENT_INSTRUCTIONS.md").read_text(encoding="utf-8")
        self.assertIn("## Merge Continuation", text)
        self.assertIn("merge or enable platform auto-merge without asking", text)
        self.assertIn("required CI/status checks are passing", text)

    def test_run_prompt_keeps_merge_as_routine_step(self) -> None:
        text = (ROOT / "prompts/run-task.md").read_text(encoding="utf-8")
        self.assertIn("If CI/status checks pass and merge gates are satisfied", text)
        self.assertIn("merge or enable platform auto-merge without asking", text)


if __name__ == "__main__":
    unittest.main()
