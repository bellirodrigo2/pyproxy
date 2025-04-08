from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import (
    Any,
    Generic,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
    runtime_checkable,
    ContextManager,  # alias to avoid conflict
)

# === Handler Protocols ===

@runtime_checkable
class GetHandler(Protocol):
    """Intercepts attribute access: proxy.attr.
    The attribute name is provided by the key of the dict, so it is not passed to the function.
    """
    def __call__(self, obj: Any) -> Any: ...


@runtime_checkable
class SetHandler(Protocol):
    """Intercepts attribute assignment: proxy.attr = value.
    The attribute name is provided by the key of the dict, so it is not passed to the function.
    """
    def __call__(self, obj: Any, value: Any) -> None: ...


@runtime_checkable
class HasHandler(Protocol):
    """Intercepts membership checks: 'x' in proxy"""
    def __call__(self, obj: Any, prop: str) -> bool: ...


@runtime_checkable
class DeleteHandler(Protocol):
    """Intercepts attribute deletion: del proxy.attr"""
    def __call__(self, obj: Any, prop: str) -> None: ...


@runtime_checkable
class CallHandler(Protocol):
    """Intercepts function/method calls: proxy(*args, **kwargs)"""
    def __call__(self, target: Any, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class CreateHandler(Protocol):
    """Intercepts object instantiation (constructor-like): proxy.create(...)"""
    def __call__(self, target: Any, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class ContextHandler(Protocol):
    """Intercepts context manager usage: with proxy as x"""
    def __call__(self, obj: Any) -> ContextManager[Any]: ...


@dataclass
class Handler:
    """
    A collection of optional handler functions that can intercept operations
    on a proxied object. Inspired by JavaScript Proxy handlers such as `get`, `set`, etc.

    Attributes:
        get (Optional[dict[str, GetHandler]]): Intercepts attribute access.
            Each key in the dictionary corresponds to an attribute name; its value is a function
            that receives the target and returns the intercepted value.
            The client may optionally include a catch‐all handler under the key "__get_attr__".
        set (Optional[dict[str, SetHandler]]): Intercepts attribute assignment.
            Each key corresponds to an attribute name; its value is a function that receives the target and the new value.
            The client may optionally include a catch‐all handler under the key "__set_attr__".
        has (Optional[HasHandler]): Intercepts membership tests (`in`).
        delete (Optional[DeleteHandler]): Intercepts attribute deletion.
        call (Optional[CallHandler]): Intercepts function or method calls.
        create (Optional[CreateHandler]): Intercepts object instantiation (constructor-like behavior).
        context (Optional[ContextHandler]): Intercepts context manager usage (`with proxy as x:`).
    """
    get: Optional[dict[str, GetHandler]] = None
    set: Optional[dict[str, SetHandler]] = None
    has: Optional[HasHandler] = None
    delete: Optional[DeleteHandler] = None
    call: Optional[CallHandler] = None
    create: Optional[CreateHandler] = None
    context: Optional[ContextHandler] = None

    def __post_init__(self) -> None:
        # Check each handler field to ensure, if provided, it is callable.
        # For 'get' and 'set', we expect a dict mapping strings to callables.
        hints = get_type_hints(self.__class__)
        for field_name in hints:
            value = getattr(self, field_name)
            if value is None:
                continue
            if field_name in ("get", "set"):
                if not isinstance(value, dict):
                    raise TypeError(f"Handler field '{field_name}' must be a dict mapping attribute names to callables")
                for key, func in value.items():
                    if not callable(func):
                        raise TypeError(f"Handler field '{field_name}' for key '{key}' must be callable")
            else:
                if not callable(value):
                    raise TypeError(f"Handler field '{field_name}' must be callable")


# === Proxy Metaclass for __instancecheck__ spoofing ===

class ProxyMeta(type):
    def __instancecheck__(cls, instance: Any) -> bool:
        # Avoid recursion using type() instead of isinstance()
        if type(instance) is Proxy and getattr(instance, "__spoof_class__", False):
            return True
        return False


T = TypeVar("T")
C = TypeVar("C", bound=CallHandler)
K = TypeVar("K", bound=CreateHandler)


@dataclass
class Proxy(Generic[T], metaclass=ProxyMeta):
    """
    A Python implementation of JavaScript-like Proxy objects.

    Intercepts operations on the `target` object using the provided `handler`.
    Useful for injecting logic like logging, validation, lazy loading, etc.

    Attributes:
        target (T): The underlying object being proxied.
        handler (Handler): A set of interception hooks.
    
    Methods:
        wrap: Class method to create a Proxy with optional class spoofing.
        create: Mimics object construction.
        __call__: Allows proxy to behave like a callable if target is callable.
        __getattr__, __setattr__, __delattr__, __contains__: Intercept standard attribute operations.
        __getitem__, __setitem__: Intercept subscript (item) access and assignment.
        __enter__, __exit__: Handle context manager operations.
    """
    target: T
    handler: Handler = field(default_factory=Handler)
    __is_proxy__: bool = field(init=False, default=True)

    def __post_init__(self) -> None:
        if not isinstance(self.handler, Handler):
            raise TypeError("handler must be an instance of Handler")

    def __getattr__(self, name: str) -> Any:
        if self.handler.get:
            # Look for a specific handler for this attribute.
            func = self.handler.get.get(name)
            # If not found, try a catch-all under the key "__get_attr__".
            if func is None:
                func = self.handler.get.get("__get_attr__")
            if func is not None:
                return func(self.target)
        return getattr(self.target, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"target", "handler", "__is_proxy__", "__spoof_class__"}:
            super().__setattr__(name, value)
        else:
            if self.handler.set:
                func = self.handler.set.get(name)
                if func is None:
                    func = self.handler.set.get("__set_attr__")
                if func is not None:
                    return func(self.target, value)
            setattr(self.target, name, value)

    def __delattr__(self, name: str) -> None:
        if self.handler.delete:
            self.handler.delete(self.target, name)
        else:
            delattr(self.target, name)

    def __contains__(self, item: str) -> bool:
        if self.handler.has:
            return self.handler.has(self.target, item)
        return hasattr(self.target, item)

    def __getitem__(self, key: Any) -> Any:
        if self.handler.get:
            func = self.handler.get.get(key)
            if func is None:
                func = self.handler.get.get("__get_attr__")
            if func is not None:
                return func(self.target)
        return self.target[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        if self.handler.set:
            func = self.handler.set.get(key)
            if func is None:
                func = self.handler.set.get("__set_attr__")
            if func is not None:
                return func(self.target, value)
        self.target[key] = value

    def __call__(self: "Proxy[C]", *args: Any, **kwargs: Any) -> Any:
        if self.handler.call:
            return self.handler.call(self.target, *args, **kwargs)
        return self.target(*args, **kwargs)

    def create(self: "Proxy[K]", *args: Any, **kwargs: Any) -> Any:
        if self.handler.create:
            return self.handler.create(self.target, *args, **kwargs)
        return self.target(*args, **kwargs)

    def __enter__(self) -> Any:
        """
        Enters the runtime context by delegating to the target's or the context handler's __enter__.
        Returns:
            Any: The object returned by the target's __enter__.
        """
        if self.handler.context:
            return self.handler.context(self.target).__enter__()  # type: ignore[attr-defined]
        if isinstance(self.target, AbstractContextManager):
            return self.target.__enter__()  # type: ignore[attr-defined]
        raise TypeError(f"Target object of type {type(self.target).__name__} is not a context manager")

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Optional[bool]:
        """
        Exits the runtime context by delegating to the target's or the context handler's __exit__.
        Returns:
            Optional[bool]: The result of the __exit__ method.
        """
        if self.handler.context:
            return self.handler.context(self.target).__exit__(exc_type, exc_val, exc_tb)  # type: ignore[attr-defined]
        if isinstance(self.target, AbstractContextManager):
            return self.target.__exit__(exc_type, exc_val, exc_tb)  # type: ignore[attr-defined]
        raise TypeError(f"Target object of type {type(self.target).__name__} is not a context manager")

    @classmethod
    def wrap(cls, target: T, handler: Handler, spoof_class: bool = False) -> "Proxy[T]":
        """
        Wraps a target object with a Proxy using the provided handler.

        Args:
            target (T): The object to be wrapped.
            handler (Handler): A set of interception hooks (get, set, call, etc).
            spoof_class (bool): If True, marks the Proxy instance to spoof the class
                of the target. This allows isinstance(proxy, TargetClass) to return True
                (as determined by the custom __instancecheck__ in the metaclass).
                If False, isinstance(proxy, TargetClass) will return False by default,
                but you can still check the underlying type using isinstance(proxy.target, TargetClass)
                or by using a utility like unwrap(proxy).

        Returns:
            Proxy[T]: An instance of Proxy wrapping the target.
        """
        instance = cls.__new__(cls)
        super(cls, instance).__setattr__("target", target)
        super(cls, instance).__setattr__("handler", handler)
        instance.__post_init__()
        if spoof_class:
            object.__setattr__(instance, "__spoof_class__", True)
        return instance


def is_proxy(obj: Any) -> bool:
    """
    Checks whether the given object is an instance of Proxy.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if the object is a Proxy, False otherwise.
    """
    return getattr(obj, "__is_proxy__", False)


def unwrap(obj: Union[T, Proxy[T]], max_depth: int = 10) -> T:
    """
    Recursively unwraps nested Proxy objects to retrieve the original target.

    This function checks if the object is a Proxy instance and extracts the
    `.target` field until it reaches a non-Proxy object, or until max_depth is hit.

    Args:
        obj: The object to unwrap (may be a Proxy or nested Proxies).
        max_depth: Maximum levels of Proxy unwrapping to prevent infinite loops.

    Returns:
        The innermost unwrapped object.

    Raises:
        ValueError: If a cyclic reference is detected in the Proxy chain.

    Note:
        Works regardless of spoof_class, since custom __instancecheck__ handles that.
    """
    seen: set[int] = set()
    depth = 0
    while isinstance(obj, Proxy) and depth < max_depth:
        proxy = cast(Proxy[Any], obj)
        obj_id = id(proxy)
        if obj_id in seen:
            raise ValueError("Cycle detected in Proxy unwrap chain")
        seen.add(obj_id)
        obj = proxy.target
        depth += 1
    return cast(T, obj)
