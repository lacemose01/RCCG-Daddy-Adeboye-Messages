import unittest
from datetime import datetime, timezone

from generate_playlist import next_schedule_time, update_schedules


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.old = [{"title": "Old", "speaker": "Grace Radio", "url": "https://res.cloudinary.com/a", "durationSeconds": 60}]
        self.new = [{"title": "New", "speaker": "Grace Radio", "url": "https://res.cloudinary.com/b", "durationSeconds": 60}]

    def test_update_starts_at_a_cycle_boundary_at_least_five_minutes_away(self):
        now = datetime(2026, 1, 1, 0, 0, 15, tzinfo=timezone.utc)
        self.assertEqual(next_schedule_time(self.start, self.old, now).isoformat(), "2026-01-01T00:06:00+00:00")

    def test_existing_schedule_is_preserved_and_unchanged_input_does_not_add_one(self):
        now = datetime(2026, 1, 1, 0, 0, 15, tzinfo=timezone.utc)
        schedules = [{"startAt": "2026-01-01T00:00:00Z", "tracks": self.old}]
        updated = update_schedules(schedules, self.new, now)
        self.assertEqual(updated[0], schedules[0])
        self.assertEqual(updated[1]["startAt"], "2026-01-01T00:06:00.000Z")
        self.assertEqual(update_schedules(updated, self.new, now), updated)

    def test_updates_queued_before_activation_wait_for_a_complete_cycle(self):
        now = datetime(2026, 1, 1, 0, 0, 15, tzinfo=timezone.utc)
        schedules = [
            {"startAt": "2026-01-01T00:00:00Z", "tracks": self.old},
            {"startAt": "2026-01-01T00:06:00Z", "tracks": self.new},
        ]
        updated = update_schedules(schedules, self.old, now)
        self.assertEqual(updated[-1]["startAt"], "2026-01-01T00:07:00.000Z")


if __name__ == "__main__":
    unittest.main()
