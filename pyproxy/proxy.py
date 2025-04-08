from dataclasses import dataclass, field
from typing import Any, Generic, Iterable, Optional, Protocol, TypeVar, runtime_checkable


T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)

@runtime_checkable
class GetHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> Any: ...
    
@runtime_checkable
class SetHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, value: Any) -> Any: ...
    
@runtime_checkable
class HasHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> bool: ...

@runtime_checkable
class DeleteHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> None: ...
    
@runtime_checkable
class CallHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, *args: Any, **kwargs: Any) -> Any: ...
    
@dataclass
class Handler(Generic[T]):
    get: Optional[dict[str, GetHandler[T]]] = None
    set: Optional[dict[str, SetHandler[T]]] = None
    has: Optional[dict[Any, HasHandler[T]]] = None
    delete: Optional[dict[str, DeleteHandler[T]]] = None
    call: Optional[dict[str, CallHandler[T]]] = None
    
@dataclass
class Proxy(Generic[T]):
    target: T
    handler: Handler[T] 
    __is_proxy__: bool = field(init=False, default=True)
    
    def __post_init__(self) -> None:
        if not isinstance(self.handler, Handler):
            raise TypeError("handler must be an instance of Handler")

    def __getattr__(self, name: str) -> Any:
        
        if self.handler.call:
            func = self.handler.call.get(name)
            if func is not None:
                return lambda *args, **kwargs: func(self.target, *args, **kwargs)
        
        if self.handler.get:
            func = self.handler.get.get(name)
            if func is not None:
                return func(self.target)
        return getattr(self.target, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"target", "handler", "__is_proxy__"}:
            return super().__setattr__(name, value)

        if self.handler.set:
            func = self.handler.set.get(name)
            if func is not None:
                return func(self.target, value)

        setattr(self.target, name, value)
    
    def __delattr__(self, name: str) -> None:
        if self.handler.delete:
            func = self.handler.delete.get(name)
            if func is not None:
                return func(self.target)

        delattr(self.target, name)
        
    def __contains__(self, name: object) -> bool:
        if self.handler.has:
            func = self.handler.has.get(name)
            if func:
                return func(self.target)

        if isinstance(self.target, Iterable):
            try:
                return name in self.target
            except TypeError:
                pass
            
        if isinstance(name, str):
            return hasattr(self.target, name)

        return False
