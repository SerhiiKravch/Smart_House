from django.test import TestCase

from apps.automation.rules import (
    is_night_time,
    should_turn_on_at_day,
    should_turn_on_at_night,
)


class AutomationRulesTests(TestCase):
    def test_is_night_time_for_wrapped_window(self):
        self.assertTrue(is_night_time(hour=23, start_hour=23, end_hour=7))
        self.assertTrue(is_night_time(hour=2, start_hour=23, end_hour=7))
        self.assertFalse(is_night_time(hour=12, start_hour=23, end_hour=7))

    def test_day_threshold_is_configurable(self):
        self.assertTrue(should_turn_on_at_day(1300, 1200))
        self.assertFalse(should_turn_on_at_day(1100, 1200))

    def test_night_thresholds_are_configurable(self):
        self.assertTrue(should_turn_on_at_night(60, 50, 50, 0))
        self.assertFalse(should_turn_on_at_night(40, 50, 50, 0))
