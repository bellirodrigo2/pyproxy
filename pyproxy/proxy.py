from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import (
    Any,
    ContextManager,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)


@runtime_checkable
class GetHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> Any: ...


@runtime_checkable
class SetHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, value: Any) -> Any: ...


@runtime_checkable
class ContainHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, value: Any) -> Any: ...


@runtime_checkable
class DeleteHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> None: ...


@runtime_checkable
class CallHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class ContextHandler(Protocol):
    def __call__(self, target: Any) -> ContextManager[Any]: ...


@runtime_checkable
class IteratorHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> Any: ...
@runtime_checkable
class StrHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> Any: ...
@runtime_checkable
class ReprHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> Any: ...


@runtime_checkable
class GetItemHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, key: str) -> Any: ...


@runtime_checkable
class LenHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> int: ...


@runtime_checkable
class SetItemHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, key: Any, value: Any) -> None: ...


@runtime_checkable
class EqualHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, other: Any) -> bool: ...


@runtime_checkable
class NEqualHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra, other: Any) -> bool: ...


@runtime_checkable
class BoolHandler(Protocol[T_contra]):
    def __call__(self, target: T_contra) -> bool: ...


@dataclass
class Handler(Generic[T]):
    get: Optional[dict[str, GetHandler[T]]] = None
    set: Optional[dict[str, SetHandler[T]]] = None
    contain: Optional[ContainHandler[T]] = None
    delete: Optional[dict[str, DeleteHandler[T]]] = None
    call: Optional[dict[str, CallHandler[T]]] = None
    context: Optional[ContextHandler] = None
    iterator: Optional[IteratorHandler[T]] = None
    str: Optional[StrHandler[T]] = None
    repr: Optional[ReprHandler[T]] = None
    getitem: Optional[GetItemHandler[T]] = None
    setitem: Optional[SetItemHandler[T]] = None
    len: Optional[LenHandler[T]] = None
    eq: Optional[EqualHandler[T]] = None
    ne: Optional[NEqualHandler[T]] = None
    bool: Optional[BoolHandler[T]] = None


PROTECTED_FIELDS = {
    "target",
    "handler",
    "__is_proxy__",
    "_iter",
    "__spoof_class__",
    "__strict__",
}


@dataclass
class Proxy(Generic[T]):
    target: T
    handler: Handler[T]
    __is_proxy__: bool = field(init=False, default=True)
    __strict__: bool = field(init=False, default=False)
    _iter: Optional[Iterator[Any]] = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.handler, Handler):  # type: ignore
            raise TypeError("handler must be an instance of Handler")

    def _check_strict(self, name: object, context: str = "access") -> None:
        if self.__strict__:
            raise AttributeError(
                f"Strict mode: cannot {context} attribute '{name}' not listed in handler."
            )

    def __getattr__(self, name: str) -> Any:
        if self.handler.call:
            func = self.handler.call.get(name)
            if func is not None:
                return lambda *args, **kwargs: func(self.target, *args, **kwargs)  # type: ignore

        if self.handler.get:
            func = self.handler.get.get(name)
            if func is not None:
                return func(self.target)

        self._check_strict(name, "get")
        return getattr(self.target, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in PROTECTED_FIELDS:
            raise AttributeError(f"Cannot set protected field '{name}' from Proxy.")

        if self.handler.set:
            func = self.handler.set.get(name)
            if func is not None:
                return func(self.target, value)
        self._check_strict(name, "set")
        setattr(self.target, name, value)

    def __delattr__(self, name: str) -> None:
        if name in PROTECTED_FIELDS:
            raise AttributeError(f"Cannot delete protected field '{name}' from Proxy.")

        if self.handler.delete:
            func = self.handler.delete.get(name)
            if func is not None:
                return func(self.target)
        self._check_strict(name, "delete")
        delattr(self.target, name)

    def __contains__(self, name: object) -> bool:
        if self.handler.contain:
            return self.handler.contain(self.target, name)
        self._check_strict(name, "check contain")
        if isinstance(self.target, Iterable):
            try:
                return name in self.target  # type: ignore
            except TypeError:
                pass

        if isinstance(name, str):
            return hasattr(self.target, name)  # type: ignore

        return False

    def __enter__(self) -> T:
        self._check_strict("__enter__", "enter context")

        if self.handler.context:
            self._ctx = self.handler.context(self.target)
            return self._ctx.__enter__()

        if not hasattr(self.target, "__enter__") or not hasattr(
            self.target, "__exit__"
        ):
            raise TypeError("Target does not support context manager protocol")

        return cast(ContextManager[Any], self.target).__enter__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if hasattr(self, "_ctx"):
            try:
                return self._ctx.__exit__(exc_type, exc_val, exc_tb)
            finally:
                del self._ctx
        self._check_strict("__exit__", "exit context")
        return cast(ContextManager[Any], self.target).__exit__(
            exc_type, exc_val, exc_tb
        )

    def __iter__(self) -> Iterable[Any]:
        if self.handler.iterator:
            return iter(self.handler.iterator(self.target))
        self._check_strict("iterator")
        return iter(self.target)  # type: ignore

    def __next__(self) -> Any:
        if not hasattr(self, "_iter") or self._iter is None:
            object.__setattr__(self, "_iter", iter(self))  # evita __setattr__
        self._check_strict("next")
        return next(self._iter)  # type: ignore

    def __getattribute__(self, name: str):  # type: ignore
        if name == "__class__" and getattr(self, "__spoof_class__", False):
            return type(object.__getattribute__(self, "target"))  # type: ignore
        return object.__getattribute__(self, name)

    def __str__(self) -> str:
        if self.handler.str:
            return self.handler.str(self.target)
        self._check_strict("'str'")
        return str(self.target)

    def __repr__(self) -> str:
        if self.handler.repr:
            return self.handler.repr(self.target)
        self._check_strict("'repr'")
        return repr(self.target)

    def __getitem__(self, key: Any) -> Any:
        if self.handler.getitem:
            return self.handler.getitem(self.target, key)
        self._check_strict("getitem")
        return self.target[key]  # type: ignore

    def __setitem__(self, key: Any, value: Any) -> None:
        if self.handler.setitem:
            return self.handler.setitem(self.target, key, value)
        self._check_strict("setitem")
        self.target[key] = value  # type: ignore

    def __len__(self) -> int:
        if self.handler.len:
            return self.handler.len(self.target)
        self._check_strict("len")
        return len(self.target)  # type: ignore

    def __eq__(self, other: Any) -> bool:
        if self.handler.eq:
            return self.handler.eq(self.target, other)
        self._check_strict("eq")
        return self.target == other  # type: ignore

    def __ne__(self, other: Any) -> bool:
        if self.handler.ne:
            return self.handler.ne(self.target, other)
        self._check_strict("ne")
        return self.target != other  # type: ignore

    def __bool__(self) -> bool:
        if self.handler.bool:
            return self.handler.bool(self.target)
        self._check_strict("bool")
        return bool(self.target)


def is_proxy(target: Any) -> bool:
    return getattr(target, "__is_proxy__", False)


PreHook = Callable[[T, Handler[T], dict[str, Any]], None]
PostHook = Callable[[Proxy[T], dict[str, Any]], None]

Hook = Union[PreHook[T], PostHook[T]]


def wrap(
    target: T,
    handler: Handler[T],
    *,
    strict: bool = False,
    spoof_class: bool = False,
    pre_hook: Optional[
        Union[
            PreHook[T],
            tuple[PreHook[T], dict[str, Any]],
        ]
    ] = None,
    post_hook: Optional[
        Union[
            PostHook[T],
            tuple[PostHook[T], dict[str, Any]],
        ]
    ] = None,
) -> Proxy[T]:
    def call_hook(
        hook: Optional[
            Union[Callable[..., None], tuple[Callable[..., None], dict[str, Any]]]
        ],
        *args: Any,
    ) -> None:
        if hook is None:
            return
        if isinstance(hook, tuple):
            func, extra = hook  # type: ignore
            func(*args, extra)
        else:
            hook(*args, {})

    call_hook(pre_hook, target, handler)

    proxy: Proxy[T] = Proxy.__new__(Proxy)
    object.__setattr__(proxy, "target", target)
    object.__setattr__(proxy, "handler", handler)
    object.__setattr__(proxy, "strict", strict)
    object.__setattr__(proxy, "__is_proxy__", True)
    object.__setattr__(proxy, "_iter", None)
    if spoof_class:
        object.__setattr__(proxy, "__spoof_class__", True)

    proxy.__post_init__()

    call_hook(post_hook, proxy)

    return proxy


def unwrap(target: Union[T, Proxy[T]]) -> T:
    if is_proxy(target):
        return getattr(target, "target")
    return target  # type: ignore


def deep_unwrap(target: Any) -> Any:
    while is_proxy(target):
        target = unwrap(target)
    return target
