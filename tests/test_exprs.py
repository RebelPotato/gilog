import pytest
import gilog as gi
import snoop

def test_basic_terms():
    assert gi.eq(gi.Wat, gi.Wat)
    assert gi.eq(gi.Type, gi.Type)
    assert gi.eq(gi.Bool, gi.Bool)
    with pytest.raises(TypeError):
        gi.eq(gi.Wat, gi.Type)
        
def test_x_eq_x():
    x = gi.var("x", gi.Type)
    snoop.pp(str(gi.eq(x, x)))
    