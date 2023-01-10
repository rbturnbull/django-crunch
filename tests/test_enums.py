from crunch.django.app.enums import Stage, State

def test_state_enum():
    assert str(State.START) == "1"
    assert str(State.SUCCESS) == "2"
    assert str(State.FAIL) == "3"        


def test_stage_enum():
    assert str(Stage.SETUP) == "1"
    assert str(Stage.WORKFLOW) == "2"
    assert str(Stage.UPLOAD) == "3"            