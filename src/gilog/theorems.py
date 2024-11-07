from .terms import Term, Var, Eq, App, Fn
from typing import List, Self


def merge(ifs1: List[Term], ifs2: List[Term]) -> List[Term]:
    """Merge two lists of terms."""
    ret = ifs1.copy()
    for if_ in ifs2:
        if not if_ in ret:
            ret.append(if_)
    return ret

def remove(ifs: List[Term], term: Term) -> List[Term]:
    """Remove a term from a list of terms."""
    return [if_ for if_ in ifs if if_ != term]

def should_eq(x: Term, y: Term):
    if x != y:
        raise AssertionError(f"{x} :: {x.type} != {y} :: {y.type}")

class Sequent:
    def __init__(self, ifs: List[Term], then: Term):
        self.ifs = ifs
        self.then = then

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Sequent)
            and self.then == value.then
            and self.ifs == value.ifs
        )

    def __repr__(self) -> str:
        return f"Sequent({repr(self.ifs)}, {repr(self.then)})"

    def __str__(self) -> str:
        return f"{', '.join(map(str, self.ifs))} ⊢ {self.then}"

    def subst(self, var: Var, expr: Term) -> Self:
        """Substitute a variable `var` with an expression `expr`."""
        return Sequent(
            [if_.subst(var, expr) for if_ in self.ifs],
            self.then.subst(var, expr),
        )


def refl(term: Term) -> Sequent:
    return Sequent([], Eq(term, term))


def trans(aIsb: Sequent, bIsc: Sequent) -> Sequent:
    assert isinstance(aIsb.then, Eq)
    a = aIsb.then.lhs
    b0 = aIsb.then.rhs
    assert isinstance(bIsc.then, Eq)
    b1 = bIsc.then.lhs
    c = bIsc.then.rhs
    should_eq(b0, b1)
    return Sequent(merge(aIsb.ifs, bIsc.ifs), Eq(a, c))


def app(opThm: Sequent, argThm: Sequent) -> Sequent:
    assert isinstance(opThm.then, Eq)
    op0 = opThm.then.lhs
    op1 = opThm.then.rhs
    assert isinstance(argThm.then, Eq)
    arg0 = argThm.then.lhs
    arg1 = argThm.then.rhs
    return Sequent(merge(opThm.ifs, argThm.ifs), Eq(App(op0, arg0), App(op1, arg1)))

def abs(var: Var, bodyThm: Sequent) -> Sequent:
    assert isinstance(bodyThm.then, Eq)
    lhs = bodyThm.then.lhs
    rhs = bodyThm.then.rhs
    for if_ in bodyThm.ifs:
        if var in if_.free:
            raise ValueError(f"Variable appears free in {if_}")
    
    then = Eq(Fn(var, lhs), Fn(var, rhs))
    return Sequent(remove(bodyThm.ifs, var), then)

def step(op: Term, arg: Term) -> Sequent:
    assert isinstance(op, Fn)
    return Sequent([], Eq(App(op, arg), op.apply(arg)))

def assume(term: Term) -> Sequent:
    return Sequent([term], term)

def emp(pqThm, pThm) -> Sequent:
    p = pThm.then
    assert isinstance(pqThm.then, Eq)
    p0 = pThm.then.rhs
    q = pqThm.then.rhs
    should_eq(p, p0)
    return Sequent(merge(pqThm.ifs, pThm.ifs), q)

def deduct(aThm, bThm) -> Sequent:
    a = aThm.then
    b = bThm.then
    return Sequent(merge(remove(bThm.ifs, a), remove(aThm.ifs, b)), Eq(a, b))

def eq_def(lhs, rhs) -> Sequent:
    x = Var("x", lhs.type)
    y = Var("y", rhs.type)
    eqTerm = Fn(x, Fn(y, Eq(x, y)))
    return Sequent([], Eq(Eq(lhs, rhs), App(App(eqTerm, lhs), rhs)))