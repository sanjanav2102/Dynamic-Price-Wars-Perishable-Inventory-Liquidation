
class SimulationMetrics:
    def __init__(self):
        self.total_revenue = 0.0
        self.units_sold = 0
        self.successful_deals = 0
        self.failed_negotiations = 0
        self.rejected_offers = 0

    def record_successful_deal(
        self,
        quantity: int,
        unit_price: float,
    ) -> None:
        self.total_revenue += quantity * unit_price
        self.units_sold += quantity
        self.successful_deals += 1

    def record_failed_negotiation(self) -> None:
        self.failed_negotiations += 1

    def record_rejected_offer(self) -> None:
        self.rejected_offers += 1

    def get_summary(self) -> dict:
        return {
            "total_revenue": round(self.total_revenue, 2),
            "units_sold": self.units_sold,
            "successful_deals": self.successful_deals,
            "failed_negotiations": self.failed_negotiations,
            "rejected_offers": self.rejected_offers,
        }
