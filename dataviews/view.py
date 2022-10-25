import io
import os
import pickle
import warnings
from pathlib import Path
from typing import Any, Callable, Tuple, Union

import dill

__all__ = [
    "View",
]


Target = Union[str, Path, "View"]
Targets = Union[Target, Tuple[Target, ...]]
Loader = Callable[..., Any]
Persister = Callable[[Any, Path], None]


def default_persist(obj: Any, path: Path):
    """
    Default object persist function using pickle.
    """
    with path.open("wb") as f:
        pickle.dump(obj, f)


class View:
    """
    An unmaterialized "view" of a piece of data, represented as a set of file
    dependencies, and the logic needed to derive the data from them.

    Views are designed to be lightweight proxies for bigger pieces of data that are easy
    to compute but expensive to store. In addition, they can be used to encapsulate the
    read/write logic for custom file formats.
    """

    def __init__(
        self,
        targets: Targets,
        load: Loader,
        persist: Persister = default_persist,
    ):
        if not isinstance(targets, tuple):
            targets = (targets,)
        self._targets = tuple(self._check_target(target) for target in targets)
        self._load = load
        self._persist = persist
        self._path: Path = None
        self._cache_obj = None

    def __call__(self):
        """
        Recursively materialize the view.
        """
        if self._cache_obj is not None:
            return self._cache_obj

        def materialize(target):
            return target() if isinstance(target, View) else target

        targets = tuple(materialize(target) for target in self._targets)
        self._cache_obj = obj = self._load(*targets)
        return obj

    @staticmethod
    def _check_target(target: Target):
        """
        Validate a target. str targets are converted to Paths. Paths are resolved.
        """
        if isinstance(target, (Path, View)):
            pass
        elif isinstance(target, str):
            target = Path(target)
        else:
            raise TypeError(
                f"Got target type {type(target)}; expected str, Path, or View."
            )
        if isinstance(target, Path):
            target = target.resolve()
        return target

    def rebase_targets(self, old_parent: Path, new_parent: Path):
        """
        Recursively rebase target paths.
        """

        def _rebase(target: Target):
            assert isinstance(target, (Path, View))
            if isinstance(target, View):
                target.rebase_targets(old_parent, new_parent)
            else:
                target = Path(os.path.relpath(target, old_parent))
                target = (new_parent / target).resolve()
            return target

        self._targets = tuple(_rebase(target) for target in self._targets)

    def dump(self, f: io.IOBase, **kwargs):
        """
        Dump the (unmaterialized) view to an open file. kwargs pass through to
        `dill.dump`.
        """
        self._cache_obj = None
        dill.dump(self, f, **kwargs)

    def dumps(self, **kwargs):
        """
        Dump the (unmaterialized) view to a string. kwargs pass through to `View.dump`.
        """
        with io.StringIO() as f:
            self.dump(f, **kwargs)
            val = f.getvalue()
        return val

    def save(self, path: Union[str, Path], **kwargs):
        """
        Save the (unmaterialized) view to a path. Raises a warning if the path doesn't
        end in ".view". kwargs pass through to `View.dump`.
        """
        self._path = path = Path(path).resolve()
        if path.suffix != ".view":
            warnings.warn(
                "A .view extension is recommended for output paths", RuntimeWarning
            )
        with path.open("wb") as f:
            self.dump(f, **kwargs)

    @staticmethod
    def from_path(path: Union[str, Path]) -> "View":
        """
        Load a view from a path. Rebase the target paths if the file structure has
        changed.

        Note, the relative paths from the saved view to the targets are expected to be
        preserved.
        """
        path = Path(path).resolve()
        with path.open("rb") as f:
            view: View = dill.load(f)
        assert isinstance(view._path, Path)
        if view._path != path:
            view.rebase_targets(view._path.parent, path.parent)
        view._path = path
        return view

    @staticmethod
    def from_bytes(val: bytes) -> "View":
        """
        Load a view from bytes.
        """
        view: View = dill.loads(val)
        view._path = None

    def solidify(self, path: Union[str, Path]):
        """
        "Solidify" the materialized object (not the view) to disk.
        """
        obj = self()
        self._persist(obj, path)
