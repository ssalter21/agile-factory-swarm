from swarm_doctor import steps


def test_order_is_the_constitutions_six_steps_in_its_order():
    assert steps.ORDER == (
        "tests",
        "coverage",
        "duplication",
        "mutation",
        "crap",
        "acceptance",
    )


def test_floor_is_the_first_two_of_order_and_is_derived_from_it():
    assert steps.FLOOR == ("tests", "coverage")
    assert steps.FLOOR == steps.ORDER[:2]
