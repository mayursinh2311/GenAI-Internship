import unittest
from unittest.mock import patch

import bank_agent as ba


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


class Day26Tests(unittest.TestCase):
    def test_mask_account_number_masks_all_but_last_four(self):
        masked = ba.mask_account_number("100000001234")

        self.assertTrue(masked.endswith("1234"))
        self.assertNotIn("100000001234", masked)
        self.assertEqual(masked.count("*"), 8)

    def test_get_balance_masks_account_in_result(self):
        result = ba.get_balance("100000001234")

        self.assertIn("1234", result)
        self.assertNotIn("100000001234", result)

    def test_account_loop_stops_on_no_tool_calls(self):
        reply = make_response(content="Your account is all set.")

        with patch.object(ba, "chat", return_value=reply) as fake_chat:
            answer = ba.run_account_specialist("system", "hello", ba.account_tools)

        self.assertEqual(answer, "Your account is all set.")
        self.assertEqual(fake_chat.call_count, 1)

    def test_account_loop_caps_at_five_rounds(self):
        tool_call = _ToolCall("get_balance", '{"account_id": "100000001234"}')
        reply = make_response(tool_calls=[tool_call])

        with patch.object(ba, "chat", return_value=reply) as fake_chat:
            answer = ba.run_account_specialist("system", "loop", ba.account_tools)

        self.assertEqual(fake_chat.call_count, ba.MAX_TOOL_ROUNDS)
        self.assertIn("maximum", answer.lower())

    def test_block_card_requires_confirmation(self):
        original_status = ba.cards["CARD1234"]["status"]

        try:
            with patch.object(ba, "confirm_action", return_value=False):
                result = ba.block_card("CARD1234")

            self.assertIn("cancel", result.lower())
            self.assertEqual(ba.cards["CARD1234"]["status"], "active")

            with patch.object(ba, "confirm_action", return_value=True):
                result = ba.block_card("CARD1234")

            self.assertIn("blocked", result.lower())
            self.assertEqual(ba.cards["CARD1234"]["status"], "blocked")
        finally:
            ba.cards["CARD1234"]["status"] = original_status


if __name__ == "__main__":
    unittest.main()
