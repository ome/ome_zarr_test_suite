import glob
import os
import pathlib
import signal
import subprocess
import typing

import pytest
import yaml
from _pytest.fixtures import SubRequest


class Source:
    """
    Generic source generated from the description
    """

    def setup(self) -> None:
        pass

    def __call__(self) -> str:
        raise NotImplementedError()

    def cleanup(self) -> None:
        pass


class FileSource(Source):
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def __call__(self) -> str:
        return self.filename


class GeneratedSource(Source):
    def __init__(self, cmd: typing.List[str]) -> None:
        self.cmd = cmd

    def __call__(self) -> str:
        return subprocess.check_output(self.cmd).decode().strip()


class ProcessSource(Source):
    def __init__(self, cmd: typing.List[str], conn: str) -> None:
        self.cmd = cmd
        self.conn = conn
        self.proc: typing.Optional[subprocess.Popen[bytes]] = None

    def __call__(self) -> str:
        self.proc = subprocess.Popen(self.cmd)
        return self.conn

    def cleanup(self) -> None:
        if self.proc:
            self.proc.send_signal(signal.SIGTERM)


class Suite:
    def __init__(self, script: str) -> None:
        self.script = script

    def __call__(self, source: Source) -> None:
        path = source()
        cmd = [self.script, path]
        subprocess.check_call(cmd)


def sources() -> typing.Iterator[dict]:
    with open("sources.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    for i, doc in enumerate(docs):
        yield pytest.param(doc, id=f"source_{i}")


def suites() -> typing.Iterator[dict]:
    with open("suites.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    for i, doc in enumerate(docs):
        yield pytest.param(doc, id=f"suite_{i}")


@pytest.fixture(params=sources())
def source(request: SubRequest, tmpdir: os.PathLike) -> typing.Iterator[Source]:
    doc = request.param
    # fixdir = tmpdir / request.fixturename
    # fixdir.mkdir()
    os.chdir(tmpdir)

    # If this is a string, wrap it into a source
    if isinstance(doc, str):
        if ":" not in doc:
            # All files without a protocol should be taken relative to CWD
            _ = (pathlib.Path(f"{request.config.invocation_dir}") / doc).resolve()
            filename = str(_)
        else:
            filename = doc
        yield FileSource(filename)

    else:
        script = doc["script"]
        script = f"{request.config.invocation_dir}/scripts/{script}"
        args = doc.get("args", [])
        cmd = [script] + args

        # If a connection is defined, then this is a background process
        if "connection" in doc:
            conn = doc["connection"]
            yield ProcessSource(cmd, conn)

        # Otherwise, run the generator which will produce a string
        else:
            yield GeneratedSource(cmd)  # FIXME: how to clean up?


@pytest.fixture(params=suites())
def suite(request: SubRequest, tmpdir: os.PathLike) -> typing.Iterator[Suite]:
    doc = request.param
    script = doc["script"]
    script = f"{request.config.invocation_dir}/scripts/{script}"
    yield Suite(script)


def test(source: Source, suite: Suite) -> None:
    source.setup()
    try:
        suite(source)
    finally:
        source.cleanup()


def test_all_scripts_used() -> None:
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
