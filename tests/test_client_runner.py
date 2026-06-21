import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ClientRunnerSmokeTest(unittest.TestCase):
    def make_worktree(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="client-runner-test-"))
        self.addCleanup(shutil.rmtree, tmp)
        work = tmp / "harness"
        shutil.copytree(
            ROOT,
            work,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "state/_local/*"),
        )
        return work

    def run_client_runner(self, work: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/client_runner.py", "run", *args],
            cwd=work,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_dry_run_writes_prompt_and_record(self) -> None:
        work = self.make_worktree()

        result = self.run_client_runner(work, "--task-id", "example-smoke", "--role", "implementer")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertTrue(Path(payload["prompt_file"]).exists())
        self.assertTrue(Path(payload["record_file"]).exists())

        state = json.loads((work / "state/tasks/example-smoke.json").read_text(encoding="utf-8"))
        self.assertTrue(state["client_runs"][-1]["dry_run"])

    def test_execute_stdin_command_records_output(self) -> None:
        work = self.make_worktree()
        command = f'{sys.executable} -c "import sys; print(sys.stdin.read()[:32])"'

        result = self.run_client_runner(
            work,
            "--task-id",
            "example-smoke",
            "--role",
            "implementer",
            "--command",
            command,
            "--execute",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "executed")
        record = json.loads(Path(payload["record_file"]).read_text(encoding="utf-8"))
        self.assertFalse(record["dry_run"])
        self.assertIn("Read the repository agent", record["stdout_excerpt"])


if __name__ == "__main__":
    unittest.main()
