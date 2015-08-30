import os
import json

from textwrap import dedent
from os.path import join

from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderList(BaseTestApp):

    def _release(self, assignment, exchange, cache, course_dir, course="abc101"):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", assignment, "p1.ipynb"))
        run_python_module([
            "nbgrader", "release", assignment,
            "--course", course,
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _fetch(self, assignment, exchange, cache, course="abc101"):
        run_python_module([
            "nbgrader", "fetch", assignment,
            "--course", course,
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _submit(self, assignment, exchange, cache, course="abc101"):
        run_python_module([
            "nbgrader", "submit", assignment,
            "--course", course,
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ])

    def _list(self, exchange, cache, assignment=None, flags=None, retcode=0):
        cmd = [
            "nbgrader", "list",
            "--TransferApp.cache_directory={}".format(cache),
            "--TransferApp.exchange_directory={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)
        if assignment is not None:
            cmd.append(assignment)

        return run_python_module(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "list", "--help-all"])

    def test_list_released(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        self._release("ps1", exchange, cache, course_dir, course="xyz200")
        assert self._list(exchange, cache, "ps1", flags=["--course", "abc101"]) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            """
        ).lstrip()
        assert self._list(exchange, cache, "ps1", flags=["--course", "xyz200"]) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] xyz200 ps1
            """
        ).lstrip()
        assert self._list(exchange, cache, "ps1") == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            [ListApp | INFO] xyz200 ps1
            """
        ).lstrip()

        self._release("ps2", exchange, cache, course_dir)
        self._release("ps2", exchange, cache, course_dir, course="xyz200")
        assert self._list(exchange, cache, "ps2") == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps2
            [ListApp | INFO] xyz200 ps2
            """
        ).lstrip()

        assert self._list(exchange, cache) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            [ListApp | INFO] abc101 ps2
            [ListApp | INFO] xyz200 ps1
            [ListApp | INFO] xyz200 ps2
            """
        ).lstrip()

    def test_list_fetched(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        self._release("ps2", exchange, cache, course_dir)
        self._fetch("ps1", exchange, cache)
        assert self._list(exchange, cache) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1 (already downloaded)
            [ListApp | INFO] abc101 ps2
            """
        ).lstrip()

    def test_list_remove_outbound(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        self._release("ps2", exchange, cache, course_dir)
        self._list(exchange, cache, "ps1", flags=["--remove"])
        assert self._list(exchange, cache) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps2
            """
        ).lstrip()

        self._list(exchange, cache, "ps2", flags=["--remove"])
        assert self._list(exchange, cache, "ps2") == dedent(
            """
            [ListApp | INFO] Released assignments:
            """
        ).lstrip()

    def test_list_inbound(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)

        assert self._list(exchange, cache, "ps1", flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()

        self._fetch("ps1", exchange, cache)
        self._submit("ps1", exchange, cache)
        filename, = os.listdir(os.path.join(exchange, "abc101", "inbound"))
        timestamp = filename.split("+")[2]
        assert self._list(exchange, cache, "ps1", flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamp)
        ).lstrip()

        self._submit("ps1", exchange, cache)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101", "inbound")))
        timestamps = [x.split("+")[2] for x in filenames]
        assert self._list(exchange, cache, "ps1", flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamps[0], os.environ["USER"], timestamps[1])
        ).lstrip()

    def test_list_cached(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)

        assert self._list(exchange, cache, "ps1", flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()

        self._fetch("ps1", exchange, cache)
        self._submit("ps1", exchange, cache)
        filename, = os.listdir(os.path.join(cache, "abc101"))
        timestamp = filename.split("+")[2]
        assert self._list(exchange, cache, "ps1", flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamp)
        ).lstrip()

        self._submit("ps1", exchange, cache)
        self._list(exchange, cache, "ps1", flags=["--inbound", "--remove"])
        filenames = sorted(os.listdir(os.path.join(cache, "abc101")))
        timestamps = [x.split("+")[2] for x in filenames]
        assert self._list(exchange, cache, "ps1", flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamps[0], os.environ["USER"], timestamps[1])
        ).lstrip()

    def test_list_remove_inbound(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        self._fetch("ps1", exchange, cache)
        self._release("ps2", exchange, cache, course_dir)
        self._fetch("ps2", exchange, cache)

        self._submit("ps1", exchange, cache)
        self._submit("ps2", exchange, cache)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101", "inbound")))
        timestamps = [x.split("+")[2] for x in filenames]

        self._list(exchange, cache, "ps1", flags=["--inbound", "--remove"])
        assert self._list(exchange, cache, flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps2 {}
            """.format(os.environ["USER"], timestamps[1])
        ).lstrip()
        assert len(os.listdir(os.path.join(exchange, "abc101", "inbound"))) == 1

        self._list(exchange, cache, "ps2", flags=["--inbound", "--remove"])
        assert self._list(exchange, cache, flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()
        assert len(os.listdir(os.path.join(exchange, "abc101", "inbound"))) == 0

    def test_list_remove_cached(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        self._fetch("ps1", exchange, cache)
        self._release("ps2", exchange, cache, course_dir)
        self._fetch("ps2", exchange, cache)

        self._submit("ps1", exchange, cache)
        self._submit("ps2", exchange, cache)
        filenames = sorted(os.listdir(os.path.join(cache, "abc101")))
        timestamps = [x.split("+")[2] for x in filenames]

        self._list(exchange, cache, "ps1", flags=["--cached", "--remove"])
        assert self._list(exchange, cache, flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps2 {}
            """.format(os.environ["USER"], timestamps[1])
        ).lstrip()
        assert len(os.listdir(os.path.join(cache, "abc101"))) == 1

        self._list(exchange, cache, "ps2", flags=["--cached", "--remove"])
        assert self._list(exchange, cache, flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            """
        ).lstrip()
        assert len(os.listdir(os.path.join(cache, "abc101"))) == 0

    def test_list_cached_and_inbound(self, exchange, cache):
        self._list(exchange, cache, flags=["--inbound", "--cached"], retcode=1)

    def test_list_json(self, exchange, cache, course_dir):
        self._release("ps1", exchange, cache, course_dir)
        assert self._list(exchange, cache) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1
            """
        ).lstrip()
        assert json.loads(self._list(exchange, cache, flags=["--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "released",
                "course_id": "abc101",
                "path": os.path.join(exchange, "abc101", "outbound", "ps1"),
                "notebooks": [
                    {
                        "path": os.path.join(exchange, "abc101", "outbound", "ps1", "p1.ipynb"),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]

        self._fetch("ps1", exchange, cache)
        assert self._list(exchange, cache) == dedent(
            """
            [ListApp | INFO] Released assignments:
            [ListApp | INFO] abc101 ps1 (already downloaded)
            """
        ).lstrip()
        assert json.loads(self._list(exchange, cache, flags=["--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "fetched",
                "course_id": "abc101",
                "path": os.path.abspath("ps1"),
                "notebooks": [
                    {
                        "path": os.path.abspath(os.path.join("ps1", "p1.ipynb")),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]

        self._submit("ps1", exchange, cache)
        filenames = sorted(os.listdir(os.path.join(exchange, "abc101", "inbound")))
        timestamps = [x.split("+")[2] for x in filenames]

        assert self._list(exchange, "ps1", flags=["--inbound"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamps[0])
        ).lstrip()

        submission = "{}+ps1+{}".format(os.environ["USER"], timestamps[0])
        assert json.loads(self._list(exchange, "ps1", flags=["--inbound", "--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "submitted",
                "course_id": "abc101",
                "student_id": os.environ["USER"],
                "timestamp": timestamps[0],
                "path": os.path.join(exchange, "abc101", "inbound", submission),
                "notebooks": [
                    {
                        "path": os.path.join(exchange, "abc101", "inbound", submission, "p1.ipynb"),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]
        assert json.loads(self._list(exchange, "ps1", flags=["--remove", "--inbound", "--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "removed",
                "course_id": "abc101",
                "student_id": os.environ["USER"],
                "timestamp": timestamps[0],
                "path": os.path.join(exchange, "abc101", "inbound", submission),
                "notebooks": [
                    {
                        "path": os.path.join(exchange, "abc101", "inbound", submission, "p1.ipynb"),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]

        assert self._list(exchange, cache, flags=["--cached"]) == dedent(
            """
            [ListApp | INFO] Submitted assignments:
            [ListApp | INFO] abc101 {} ps1 {}
            """.format(os.environ["USER"], timestamps[0])
        ).lstrip()

        submission = "{}+ps1+{}".format(os.environ["USER"], timestamps[0])
        assert json.loads(self._list(exchange, cache, flags=["--cached", "--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "submitted",
                "course_id": "abc101",
                "student_id": os.environ["USER"],
                "timestamp": timestamps[0],
                "path": os.path.join(cache, "abc101", submission),
                "notebooks": [
                    {
                        "path": os.path.join(cache, "abc101", submission, "p1.ipynb"),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]
        assert json.loads(self._list(exchange, cache, flags=["--remove", "--cached", "--json"])) == [
            {
                "assignment_id": "ps1",
                "status": "removed",
                "course_id": "abc101",
                "student_id": os.environ["USER"],
                "timestamp": timestamps[0],
                "path": os.path.join(cache, "abc101", submission),
                "notebooks": [
                    {
                        "path": os.path.join(cache, "abc101", submission, "p1.ipynb"),
                        "notebook_id": "p1"
                    }
                ]
            }
        ]
