from algopy import BoxMap, UInt64

from modules import AccountingModule
from smart_contracts import abi_types as typ
from smart_contracts import constants as cst
from smart_contracts import errors as err


class ActusScheduleModule(AccountingModule):
    """ACTUS schedule storage and event lookup helpers."""

    def __init__(self) -> None:
        """Initialize schedule paging state and hashes."""
        super().__init__()

        self.schedule_page = BoxMap(
            UInt64,
            typ.ExecutionSchedulePage,
            key_prefix=cst.PREFIX_ID_SCHEDULE_PAGE,
        )
        self.event_cursor = UInt64()
        self.schedule_entry_count = UInt64()

    def _schedule_page_index(self, event_id: UInt64) -> UInt64:
        """Return the schedule page index containing the given event id."""
        return event_id // UInt64(cst.SCHEDULE_PAGE_SIZE)

    def _schedule_page_offset(self, event_id: UInt64) -> UInt64:
        """Return the offset of an event within its schedule page."""
        return event_id % UInt64(cst.SCHEDULE_PAGE_SIZE)

    def _store_schedule_page(
        self, page_index: UInt64, schedule_page: typ.ExecutionSchedulePage
    ) -> None:
        """Persist a normalized schedule page."""
        self.schedule_page[page_index] = schedule_page

    def _get_schedule_entry(self, event_id: UInt64) -> typ.ExecutionScheduleEntry:
        """Load a normalized schedule entry by global event id."""
        assert event_id < self.schedule_entry_count, err.INVALID_EVENT_ID
        page_index = self._schedule_page_index(event_id)
        assert page_index in self.schedule_page, err.INVALID_SCHEDULE_PAGE
        page = self.schedule_page[page_index].copy()
        offset = self._schedule_page_offset(event_id)
        assert offset < page.length, err.INVALID_SCHEDULE_PAGE
        return page[offset].copy()
