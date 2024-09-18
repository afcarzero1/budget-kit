from abc import ABC, abstractmethod
from budgeting.core import RecurrenceType


class Asset(ABC):
    """Asset interface."""

    def __init__(self, value: float) -> None:
        """Initialize the asset."""
        self.original_value = value
        self.value = value
        self.step_counter = 0

    def step(self) -> None:
        """Develop asset one day into the future."""
        self._step()
        self.step_counter += 1

    @abstractmethod
    def _step(self) -> None:
        """Develop one day."""
        pass

    @abstractmethod
    def is_sellable(self) -> bool:
        """Return if the asset is sellable."""
        pass

    def reset(self) -> None:
        """Reset value of the asset to original value."""
        self.value = self.original_value
        self.step_counter = 0


class BankAccount(Asset):
    """Standard bank account."""

    def __init__(
        self,
        value: float,
        interest_rate: float,
        recurrence_type: RecurrenceType,
        minimum_periods: int,
        only_on_recurrence: bool,
    ) -> None:
        """
        Initialize the bank account with an interest rate and a recurrence type for compounding.

        :param value: Initial balance of the account.
        :param interest_rate: Annual interest rate as a percentage (e.g., 1.5 for 1.5%).
        :param recurrence_type: Recurrence type for interest compounding from the RecurrenceType enum.
        :param minimum_periods: The minimum number of periods that the money is locked.
        :param only_on_recurrence: Sellable only at recurrence day
        """
        super().__init__(value)
        self.only_on_recurrence = only_on_recurrence
        self.minimum_periods = minimum_periods
        self.interest_rate = interest_rate
        self.recurrence_type = recurrence_type
        self.num_periods = 0

    def _step(self) -> None:
        """Apply interest based on the recurrence type setting."""
        if self.step_counter == 0:
            return

        if self.recurrence_type == RecurrenceType.DAILY:
            self.apply_interest(365)
        elif (
            self.recurrence_type == RecurrenceType.WEEKLY and self.step_counter % 7 == 0
        ):
            self.apply_interest(52)
        elif (
            self.recurrence_type == RecurrenceType.MONTHLY
            and self.step_counter % 30 == 0
        ):
            self.apply_interest(12)

    def _is_withdrawable_at_recurrence(self) -> bool:
        """Check if the current time aligns with the recurrence period (e.g., end of month or week)."""
        if self.recurrence_type == RecurrenceType.DAILY:
            return self.num_periods % self.minimum_periods == 0
        if self.recurrence_type == RecurrenceType.WEEKLY:
            return (
                self.step_counter % 7 == 0
                and self.num_periods % self.minimum_periods == 0
            )
        if self.recurrence_type == RecurrenceType.MONTHLY:
            return (
                self.step_counter % 30 == 0
                and self.num_periods % self.minimum_periods == 0
            )
        return False

    def apply_interest(self, periods: int) -> None:
        """Apply compounded interest based on the number of periods per year."""
        rate_per_period = self.interest_rate / 100 / periods
        self.value *= 1 + rate_per_period
        self.num_periods += 1

    def is_sellable(self) -> bool:
        """Assets in a bank account."""
        if self.num_periods < self.minimum_periods:
            return False

        if self.only_on_recurrence and not self._is_withdrawable_at_recurrence():
            return False

        return True

    def __repr__(self) -> str:
        """Representation of bank account."""
        return f"{self.__class__.__name__}: {self.value}"
