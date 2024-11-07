from .terms import Term, Wat, Type, Bool, Fn, Eq, App, Var, VarStack
from typing import Self


class Rep:
    def __init__(self, term: Term):
        self.term = term
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, Rep) and self.term == value.term

    def __repr__(self) -> str:
        return f"Rep({repr(self.term)})"

    def __str__(self) -> str:
        return str(self.term)

    def __call__(self, *args) -> Self:
        ret = self.term
        for arg in args:
            ret = App(ret, arg.term)
        return Rep(ret)

    def index(self) -> int:
        """Return a hash value for the term."""
        return self.term.index(VarStack())

    def subst(self, var: Self, expr: Self) -> Self:
        """Substitute a variable `var` with an expression `expr`."""
        return Rep(self.term.subst(var.term, expr.term))


Wat = Rep(Wat())
Type = Rep(Type())
Bool = Rep(Bool())


def var(name: str, type: Rep) -> Rep:
    return Rep(Var(name, type.term))


def eq(lhs: Rep, rhs: Rep) -> Rep:
    return Rep(Eq(lhs.term, rhs.term))


def fn(*args) -> Rep:
    """Generate a function term based on the given types."""

    def decorator(fn):
        global var
        vars = [var(name, type) for (name, type) in args]
        ret = fn(*vars).term
        for var in vars.reverse():
            ret = Fn(var.term, ret)
        return Rep(ret)

    return decorator
