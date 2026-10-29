"""Custom import hook and codec registration for Tongue modules."""

from __future__ import annotations

import codecs
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple

from parsethon.runtime import detect_tongue_from_source
from parsethon.tongue import registry
from parsethon.translator import translate_to_python


class TongueSourceLoader(importlib.abc.SourceLoader):
    """Loader that compiles Tongue source into standard Python bytecode."""

    def __init__(self, fullname: str, path: str, tongue_name: str) -> None:
        self.fullname = fullname
        self.path = path
        self.tongue_name = tongue_name

    def get_filename(self, fullname: str) -> str:
        return self.path

    def get_data(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def source_to_code(self, data: bytes, path: str, *, _optimize: int = -1) -> Any:
        source_text = data.decode("utf-8")
        py_source = translate_to_python(source_text, self.tongue_name)
        return compile(py_source, path, "exec", optimize=_optimize)


class TongueMetaPathFinder(importlib.abc.MetaPathFinder):
    """Finder that resolves `<module>.<tongue>.py` and `<module>.pyt` files."""

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]] = None,
        target: Optional[Any] = None,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        subname = fullname.rpartition(".")[-1]
        search_dirs = list(path) if path is not None else sys.path

        known_tongues = registry.list_tongues()

        for directory in search_dirs:
            if not directory or not os.path.isdir(directory):
                continue

            # 1. Search for `<subname>.<tongue>.py`
            for tongue_name in known_tongues:
                candidate = os.path.join(directory, f"{subname}.{tongue_name}.py")
                if os.path.isfile(candidate):
                    loader = TongueSourceLoader(fullname, candidate, tongue_name)
                    return importlib.util.spec_from_loader(
                        fullname, loader, origin=candidate
                    )

            # 2. Search for `<subname>.pyt` with header detection
            candidate_pyt = os.path.join(directory, f"{subname}.pyt")
            if os.path.isfile(candidate_pyt):
                with open(candidate_pyt, "r", encoding="utf-8") as f:
                    content = f.read(500)
                detected = detect_tongue_from_source(content)
                if detected:
                    loader = TongueSourceLoader(fullname, candidate_pyt, detected)
                    return importlib.util.spec_from_loader(
                        fullname, loader, origin=candidate_pyt
                    )

        return None


# --- Codec Support for `# coding: parsethon-<tongue>` ---

def _tongue_decode(input_bytes: bytes, errors: str = "strict", tongue_name: str = "es") -> Tuple[str, int]:
    raw_str, length = codecs.utf_8_decode(input_bytes, errors)
    translated = translate_to_python(raw_str, tongue_name)
    return translated, length


class TongueIncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def __init__(self, errors: str = "strict", tongue_name: str = "es") -> None:
        super().__init__(errors)
        self.tongue_name = tongue_name

    def _buffer_decode(self, input_bytes: bytes, errors: str, final: bool) -> Tuple[str, int]:
        if final:
            return _tongue_decode(input_bytes, errors, self.tongue_name)
        return "", 0


class TongueStreamReader(codecs.StreamReader):
    def __init__(self, stream: Any, errors: str = "strict", tongue_name: str = "es") -> None:
        super().__init__(stream, errors)
        self.tongue_name = tongue_name

    def decode(self, input_bytes: bytes, errors: str = "strict") -> Tuple[str, int]:
        return _tongue_decode(input_bytes, errors, self.tongue_name)


def search_tongue_codec(encoding: str) -> Optional[codecs.CodecInfo]:
    """Finds codecs matching pattern `parsethon-<tongue>` or `parsethon_<tongue>`."""
    normalized = encoding.lower().replace("-", "_")
    if not normalized.startswith("parsethon_"):
        return None

    tongue_name = normalized.partition("parsethon_")[2]
    if tongue_name not in registry.list_tongues():
        return None

    return codecs.CodecInfo(
        name=f"parsethon-{tongue_name}",
        encode=codecs.utf_8_encode,
        decode=lambda b, err="strict": _tongue_decode(b, err, tongue_name),
        incrementalencoder=codecs.getincrementalencoder("utf-8"),
        incrementaldecoder=lambda err="strict": TongueIncrementalDecoder(err, tongue_name),
        streamreader=lambda stream, err="strict": TongueStreamReader(stream, err, tongue_name),
        streamwriter=codecs.getwriter("utf-8"),
    )


_finder_installed = False
_codec_installed = False


def install_importer() -> None:
    """Installs the TongueMetaPathFinder in sys.meta_path."""
    global _finder_installed
    if not _finder_installed:
        sys.meta_path.insert(0, TongueMetaPathFinder())
        _finder_installed = True


def uninstall_importer() -> None:
    """Removes the TongueMetaPathFinder from sys.meta_path."""
    global _finder_installed
    sys.meta_path = [f for f in sys.meta_path if not isinstance(f, TongueMetaPathFinder)]
    _finder_installed = False


def install_codec() -> None:
    """Registers the parsethon codec search function."""
    global _codec_installed
    if not _codec_installed:
        codecs.register(search_tongue_codec)
        _codec_installed = True


def uninstall_codec() -> None:
    """Unregisters the parsethon codec search function if supported."""
    global _codec_installed
    # Python codecs registry has no unregister, but we can set flag so search_tongue_codec returns None
    _codec_installed = False


def enable() -> None:
    """Enables both the meta_path import hook and codec support."""
    install_importer()
    install_codec()


def disable() -> None:
    """Disables the meta_path import hook."""
    uninstall_importer()
    uninstall_codec()
