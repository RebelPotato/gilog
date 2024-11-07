from abc import ABC, abstractmethod
from typing import Self
from gilog.utils import sdbm_hash, combine
import snoop


class VarCounter:
    def __init__(self):
        self.stored = {}
        self.counter = 0

    def get(self, obj):
        if not (obj in self.stored):
            self.stored[obj] = self.counter
            self.counter += 1
            return self.counter - 1
        return self.stored[obj]


class VarStack:
    def __init__(self):
        self.stored = []

    def push(self, obj):
        self.stored.append(obj)

    def pop(self):
        return self.stored.pop()

    def has(self, obj):
        return obj in self.stored

    def get(self, obj):
        return self.stored.index(obj)


# Term is the base class for all terms in the language.
class Term(ABC):

    @abstractmethod
    def __eq__(self, value: object) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self, env: VarCounter) -> str:
        pass

    @abstractmethod
    def index(self, env: VarStack) -> int:
        """Return a hash value for the term."""
        pass

    def subst(self, var, expr) -> Self:
        """
        Substitute all occurences of variable `var` with the term `expr`.
        Guaranteed to return self if `var` doesn't appear free in expr.
        """
        pass


# Kinds
class Wat(Term):
    def __init__(self):
        self.free = set()
        self.type = None

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Wat)

    def __repr__(self) -> str:
        return "Wat"

    def __str__(self) -> str:
        return "Wat"

    def index(self) -> int:
        return sdbm_hash("Wat")

    def subst(self, _var, _expr) -> Self:
        return self


class Type(Term):
    def __init__(self):
        self.free = set()
        self.type = Wat()

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Type)

    def __repr__(self) -> str:
        return "Type"

    def __str__(self) -> str:
        return "Type"

    def index(self) -> int:
        return sdbm_hash("Type")

    def subst(self, _var, _expr) -> Self:
        return self


class Bool(Term):
    def __init__(self):
        self.free = set()
        self.type = Type()

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Bool)

    def __repr__(self) -> str:
        return "Bool"

    def __str__(self) -> str:
        return "Bool"

    def index(self) -> int:
        return sdbm_hash("Bool")

    def subst(self, _var, _expr) -> Self:
        return self


# applications
class App(Term):
    def __init__(self, op: Term, arg: Term):
        self.op = op
        self.arg = arg
        self.free = op.free | arg.free
        self.type = op.type(arg.type)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, App):
            return False
        return self.op == value.op and self.arg == value.arg

    def __repr__(self) -> str:
        return f"App({repr(self.op)}, {repr(self.arg)})"

    def __str__(self, env=VarCounter()) -> str:
        return f"{self.op.__str__(env)} {self.arg.__str__(env)}"

    def index(self, env=VarStack()) -> int:
        return combine(sdbm_hash("App"), self.op.index(env), self.arg.index(env))

    def subst(self, var, expr: Term) -> Self:
        if not (var in self.free):
            return self
        return App(self.op.subst(var, expr), self.arg.subst(var, expr))


# variables
class Var(Term):
    def __init__(self, name: str, type: Term):
        self.name = name
        self.free = type.free | {self}
        self.type = type

    def __eq__(self, value: object) -> bool:
        return self is value

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return f"{self.name}#{id(self)}::{repr(self.type)}"

    def __str__(self, env=VarCounter()) -> str:
        return f"{self.name}{env.get(self)}"

    def index(self, env=VarStack()) -> int:
        if not env.has(self):
            raise ValueError(f"Cannot calculate index of free variable {self.name}")
        return env.get(self)

    def subst(self, var: Self, expr: Term) -> Term:
        if not (var in self.free):
            return self
        return expr if self == var else Var(self.name, self.type.subst(var, expr))


class Pi(Term):
    def __init__(self, x: Var, body: Term):
        inputKind = x.type
        outputKind = body.type
        # we allow the full lambda cube for now
        # I sure hope it's consistent

        self.x = x
        self.body = body
        self.free = x.type.free | (body.free - {x})
        self.type = Type()

    def __eq__(self, value: object) -> bool:
        if (not isinstance(value, Pi)) or (self.x.type != value.x.type):
            return False
        return self.body == value.body.subst(value.x, self.x)

    def __repr__(self) -> str:
        return f"Pi({repr(self.x)}, {repr(self.body)})"

    def __str__(self, env=VarCounter()) -> str:
        env.get(self.x)
        return f"Π{self.x.__str__(env)}::{self.x.type.__str__(env)}. {self.body.__str__(env)}"

    def index(self, env=VarStack()) -> int:
        env.push(self.x)
        result = combine(sdbm_hash("Pi"), self.x.type.index(env), self.body.index(env))
        env.pop()
        return result

    def subst(self, var: Var, expr: Term) -> Self:
        if not (var in self.free):
            return self
        var1 = Var(var.name, var.type)
        expr1 = expr.subst(var, var1)
        # create temporary variable for var
        # if it appears free in expr, newBody's var will substitute twice
        newX = self.x.subst(var, expr1)
        newBody = self.body.subst(self.x, newX).subst(var, expr1)
        return Pi(newX, newBody).subst(var1, var)

    def apply(self, arg):
        if arg.type != self.x.type:
            raise TypeError(f"tried to apply {arg} :: ${arg.type} to {self}")
        return self.body.subst(self.x, arg)


class Fn(Term):
    def __init__(self, x: Var, body: Term):
        self.x = x
        self.body = body
        self.free = x.type.free | (body.free - {x})
        self.type = Pi(x, body.type)

    def __eq__(self, value: object) -> bool:
        if (not isinstance(value, Fn)) or (self.x.type != value.x.type):
            return False
        return self.body == value.body.subst(value.x, self.x)

    def __repr__(self) -> str:
        return f"Fn({repr(self.x)}, {repr(self.body)})"

    def __str__(self, env=VarCounter()) -> str:
        env.get(self.x)
        return f"λ{self.x.__str__(env)}::{self.x.type.__str__(env)}. {self.body.__str__(env)}"

    def index(self, env=VarStack()) -> int:
        env.push(self.x)
        result = combine(sdbm_hash("fn"), self.x.type.index(env), self.body.index(env))
        env.pop()
        return result

    def subst(self, var, expr) -> Self:
        if not (var in self.free):
            return self
        var1 = Var(var.name, var.type)
        expr1 = expr.subst(var, var1)
        # create temporary variable for var
        # if it appears free in expr, newBody's var will substitute twice
        newX = self.x.subst(var, expr1)
        newBody = self.body.subst(self.x, newX).subst(var, expr1)
        return Fn(newX, newBody).subst(var1, var)

    def apply(self, arg):
        if arg.type != self.x.type:
            raise TypeError(f"Tried to apply {arg} :: ${arg.type} to {self}")
        return self.body.subst(self.x, arg)


class Eq(Term):
    def __init__(self, lhs: Term, rhs: Term):
        if lhs.type != rhs.type:
            raise TypeError(
                f"{lhs} :: {lhs.type} and {rhs} :: {rhs.type} are not of equal types"
            )
        self.lhs = lhs
        self.rhs = rhs
        self.free = lhs.free | rhs.free
        self.type = Bool()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Eq):
            return False
        return self.lhs == value.lhs and self.rhs == value.rhs

    def __repr__(self) -> str:
        return f"Eq({repr(self.lhs)}, {repr(self.rhs)})"

    def __str__(self, env=VarCounter()) -> str:
        return f"{self.lhs.__str__(env)} = {self.rhs.__str__(env)}"

    def index(self, env=VarStack()) -> int:
        return combine(sdbm_hash("Eq"), self.lhs.index(env), self.rhs.index(env))

    def subst(self, var, expr) -> Self:
        if not (var in self.free):
            return self
        return Eq(self.lhs.subst(var, expr), self.rhs.subst(var, expr))
