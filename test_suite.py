import glob
import os
import pathlib
import signal
import subprocess
import typing

import py
import pytest
import yaml
from _pytest.fixtures import SubRequest


class Source:
    """
    Generic source generated from the entries in sources.yml
    """

    def setup(self) -> None:
        pass

    def __call__(self) -> str:
        raise NotImplementedError()

    def cleanup(self) -> None:
        pass


class FileSource(Source):
    """
    Source with the "path" key set. The URI is assumed accessible.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def __call__(self) -> str:
        return self.filename


class GeneratedSource(Source):
    """
    Source with the "script" key set and "connection" unset.
    The script will be run and the stdout will be assumed to be a URI.
    """

    def __init__(
        self,
        cmd: typing.List[str],
        tmpdir: py.path.local,
    ) -> None:
        self.cmd = cmd
        self.cwd = tmpdir

    def __call__(self) -> str:
        return subprocess.check_output(self.cmd, cwd=str(self.cwd)).decode().strip()


class ProcessSource(Source):
    """
    Source with the "script" key and "connection" set.
    The script will be left running in the background and the
    connection will be the URI passed to suites.
    """

    def __init__(
        self,
        cmd: typing.List[str],
        conn: str,
        tmpdir: py.path.local,
    ) -> None:
        self.cmd = cmd
        self.conn = conn
        self.cwd = tmpdir
        self.proc: typing.Optional[subprocess.Popen[bytes]] = None

    def __call__(self) -> str:
        self.proc = subprocess.Popen(
            self.cmd,
            cwd=str(self.cwd),
            stdout=subprocess.PIPE,
        )

        while True:
            print("Waiting for server...")
            output = None
            if self.proc.stdout is not None:
                output = self.proc.stdout.readline()
            if self.proc.poll() is not None:
                break
            if output:
                out = output.decode().strip()
                print(f"OUT: {out}")
                if "::ready::" in out:
                    break

        return self.conn

    def cleanup(self) -> None:
        if self.proc:
            self.proc.send_signal(signal.SIGINT)


class Suite:
    """
    Entry from the suites.yml file.

    Currently only scripts are supported which will be passed
    the URI from a source.
    """

    def __init__(self, script: str) -> None:
        self.script = script

    def __call__(self, source: Source) -> None:
        path = source()
        cmd = [self.script, path]
        subprocess.check_call(cmd)


def sources() -> typing.Iterator[dict]:
    """
    generator to load all sources as pytest parameters
    """
    with open("sources.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    for i, doc in enumerate(docs):
        name = doc["name"]
        yield pytest.param(doc, id=name)


def suites() -> typing.Iterator[dict]:
    """
    generator to load all suites as pytest parameters
    """
    with open("suites.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    for i, doc in enumerate(docs):
        name = doc["name"]
        yield pytest.param(doc, id=name)


@pytest.fixture(params=sources())
def source(request: SubRequest, tmpdir: py.path.local) -> typing.Iterator[Source]:
    doc = request.param
    with tmpdir.as_cwd():

        skip = doc.get("skip", False)
        if skip:
            pytest.skip(f"skip set: {skip}")

        # If this is a string, wrap it into a source
        if "path" in doc:
            path = doc["path"]
            if ":" not in path:
                # All files without a protocol should be taken relative to CWD
                _ = (pathlib.Path(f"{request.config.invocation_dir}") / path).resolve()
                filename = str(_)
            else:
                filename = path
            yield FileSource(filename)

        else:
            script = doc["script"]
            script = f"{request.config.invocation_dir}/scripts/{script}"
            args = doc.get("args", [])
            cmd = [script] + args

            # If a connection is defined, then this is a background process
            if "connection" in doc:
                conn = doc["connection"]
                yield ProcessSource(cmd, conn, tmpdir)

            # Otherwise, run the generator which will produce a string
            else:
                yield GeneratedSource(cmd, tmpdir)


@pytest.fixture(params=suites())
def suite(request: SubRequest, tmpdir: os.PathLike) -> typing.Iterator[Suite]:
    doc = request.param
    script = doc["script"]
    idir = f"{request.config.invocation_dir}"
    os.environ["INVOCATION_DIR"] = idir
    script = f"{idir}/scripts/{script}"
    yield Suite(script)


def test(source: Source, suite: Suite) -> None:
    """
    Primary test matching all sources with all suites.
    """
    source.setup()
    try:
        suite(source)
    finally:
        source.cleanup()


def test_all_scripts_used() -> None:
    """
    Quick test to check that scripts have been registered as sources or suites.
    """
    with open("suites.yml") as o:
        suites = o.read()
    with open("sources.yml") as o:
        sources = o.read()

    missing = []
    for script in glob.glob("scripts/*"):
        script = os.path.basename(script)
        if script in suites or script in sources:
            pass
        else:
            missing.append(script)
    assert not missing
