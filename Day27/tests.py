import unittest
from unittest.mock import patch

import agents as ag


class _Function:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, name, arguments, call_id="call_1"):
        self.id = call_id
        self.function = _Function(name, arguments)


class _Message:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, message):
        self.message = message


class _Response:
    def __init__(self, message):
        self.choices = [_Choice(message)]


def make_response(content=None, tool_calls=None):
    return _Response(_Message(content=content, tool_calls=tool_calls))


class Day27Tests(unittest.TestCase):
    def test_mask_account_number_masks_all_but_last_four(self):
        masked = ag.mask_account_number("100000001234")

        self.assertTrue(masked.endswith("1234"))
        self.assertNotIn("100000001234", masked)
        self.assertEqual(masked.count("*"), 8)

    def test_get_balance_masks_account_in_result(self):
        result = ag.get_balance("100000001234")

        self.assertIn("1234", result)
        self.assertNotIn("100000001234", result)

    def test_account_loop_stops_on_no_tool_calls(self):
        reply = make_response(content="Your account is all set.")

        with patch.object(ag, "chat", return_value=reply) as fake_chat:
            answer = ag.run_account_specialist("system", "hello", ag.account_tools)

        self.assertEqual(answer, "Your account is all set.")
        self.assertEqual(fake_chat.call_count, 1)

    def test_account_loop_caps_at_five_rounds(self):
        tool_call = _ToolCall("get_balance", '{"account_id": "100000001234"}')
        reply = make_response(tool_calls=[tool_call])

        with patch.object(ag, "chat", return_value=reply) as fake_chat:
            answer = ag.run_account_specialist("loop", "loop", ag.account_tools)

        self.assertEqual(fake_chat.call_count, ag.MAX_TOOL_ROUNDS)
        self.assertIn("maximum", answer.lower())

    def test_block_card_requires_confirmation(self):
        original_status = ag.cards["CARD1234"]["status"]

        try:
            with patch.object(ag, "confirm_action", return_value=False):
                result = ag.block_card("CARD1234")

            self.assertIn("cancel", result.lower())
            self.assertEqual(ag.cards["CARD1234"]["status"], "active")

            with patch.object(ag, "confirm_action", return_value=True):
                result = ag.block_card("CARD1234")

            self.assertIn("blocked", result.lower())
            self.assertEqual(ag.cards["CARD1234"]["status"], "blocked")
        finally:
            ag.cards["CARD1234"]["status"] = original_status

    def test_route_falls_back_to_general(self):
        reply = make_response(content="weather")

        with patch.object(ag, "chat", return_value=reply):
            label = ag.route("What is the weather today?")

        self.assertEqual(label, "general")

    def test_run_specialist_collects_trace(self):
        tool_call = _ToolCall("track_booking", '{"booking_id": "BK201"}')
        first = make_response(tool_calls=[tool_call])
        second = make_response(content="Your booking is confirmed.")

        with patch.object(ag, "chat", side_effect=[first, second]):
            trace = []
            answer = ag.run_specialist("system", "Where is BK201?", ag.booking_tools, trace=trace)

        self.assertEqual(answer, "Your booking is confirmed.")
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["name"], "track_booking")


if __name__ == "__main__":
    unittest.main()
