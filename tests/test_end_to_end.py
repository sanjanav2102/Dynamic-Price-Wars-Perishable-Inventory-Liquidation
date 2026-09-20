from integration.simulation import (
    PriceWarSimulation,
)
def test_complete_simulation_runs():
    simulation = PriceWarSimulation()
    simulation.run()
    status = (
        simulation.environment.get_status()
    )

    assert (
        status["remaining_inventory"]
        >= 0
    )

    assert (
        status["expired_inventory"]
        >= 0
    )

    assert (
        status["metrics"]["total_units_sold"]
        >= 0
    )

    assert (
        status["metrics"]["total_revenue"]
        >= 0
    )