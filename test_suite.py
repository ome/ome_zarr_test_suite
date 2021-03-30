import os
import subprocess
import typing

import pytest
import yaml
from _pytest.fixtures import SubRequest


class Source:
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
        return subprocess.check_output(self.cmd).decode()


class Sink:
    def __init__(self, script: str) -> None:
        self.script = script

    def __call__(self, source: Source) -> None:
        path = source()
        cmd = [self.script, path]
        subprocess.check_call(cmd)


def inputs() -> typing.Iterator[dict]:
    with open("inputs.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    yield from docs


def suites() -> typing.Iterator[dict]:
    with open("suites.yml") as file:
        docs = yaml.load(file, Loader=yaml.FullLoader)
    yield from docs


@pytest.fixture(params=inputs())
def source(request: SubRequest, tmpdir: os.PathLike) -> typing.Iterator[Source]:
    doc = request.param
    os.chdir(tmpdir)
    if isinstance(doc, str):
        # If this is a string, wrap it into an input
        yield FileSource(doc)
    else:
        # Otherwise, run the generator which will produce a string
        script = doc["script"]
        script = f"{request.config.invocation_dir}/scripts/{script}"
        args = doc.get("args", [])
        cmd = [script] + args
        yield GeneratedSource(cmd)  # FIXME: how to clean up?


@pytest.fixture(params=suites())
def sink(request: SubRequest, tmpdir: os.PathLike) -> typing.Iterator[Sink]:
    doc = request.param
    script = doc["script"]
    script = f"{request.config.invocation_dir}/scripts/{script}"
    yield Sink(script)


def test(source: Source, sink: Sink) -> None:
    source.setup()
    try:
        sink(source)
    finally:
        source.cleanup()
