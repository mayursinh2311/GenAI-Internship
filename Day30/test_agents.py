"""Unit tests for the Day 30 hotel assistant.

Every model call is mocked, so the suite runs offline and costs nothing.
Run from this folder:  python -m unittest -v test_agents.py
"""

import copy
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import agents


def reply(content=None, tool_calls=None):
    """Build a response shaped like the Mistral and Groq SDK responses."""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_call(name, arguments, call_id="call_1"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class HotelTestCase(unittest.TestCase):
    """Reset shared demo state and keep CSV logs out of the repo."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="day30_test_")
        self.charge_log = os.path.join(self.temp_dir, "charges.csv")
        self.handoff_log = os.path.join(self.temp_dir, "handoffs.csv")

        self.patches = [
            mock.patch.object(agents, "CHARGE_LOG", self.charge_log),
            mock.patch.object(agents, "HANDOFF_LOG", self.handoff_log),
        ]
        for patcher in self.patches:
            patcher.start()

        self.rooms = copy.deepcopy(agents.ROOMS)
        self.charges = copy.deepcopy(agents.CHARGES)
        self.handoffs = list(agents.HANDOFFS)
        agents.HANDOFFS.clear()

    def tearDown(self):
        agents.ROOMS.clear()
        agents.ROOMS.update(self.rooms)
        agents.CHARGES.clear()
        agents.CHARGES.update(self.charges)
        agents.HANDOFFS.clear()
        agents.HANDOFFS.extend(self.handoffs)

        for patcher in reversed(self.patches):
            patcher.stop()


class TestRouter(HotelTestCase):
    def test_router_uses_temperature_zero_and_returns_bill(self):
        with mock.patch.object(agents, "chat", return_value=reply("bill")) as fake:
            label = agents.route("What is my balance?")

        self.assertEqual(label, "bill")
        self.assertEqual(fake.call_args.kwargs["temperature"], 0)

    def test_router_falls_back_to_general(self):
        with mock.patch.object(agents, "chat", return_value=reply("spa_booking")):
            label = agents.route("Do something odd")

        self.assertEqual(label, "general")

    def test_router_cleans_punctuation(self):
        with mock.patch.object(agents, "chat", return_value=reply("  Bill. ")):
            label = agents.route("How much do I owe?")

        self.assertEqual(label, "bill")

    def test_router_returns_none_when_model_is_down(self):
        with mock.patch.object(agents, "chat", return_value=None):
            self.assertIsNone(agents.route("Hello"))


class TestTools(HotelTestCase):
    def test_menu_returns_food_items(self):
        text = agents.get_menu("food")
        self.assertIn("club sandwich", text)

    def test_menu_rejects_unknown_category(self):
        self.assertIn("Unknown category", agents.get_menu("pizza"))

    def test_order_status_unknown(self):
        self.assertIn("not found", agents.order_status("ORD999"))

    def test_check_availability_rejects_bad_date(self):
        self.assertIn("YYYY-MM-DD", agents.check_availability("25-12-2026", "deluxe"))

    def test_check_availability_reports_rooms(self):
        text = agents.check_availability("2026-12-25", "suite")
        self.assertIn("suite", text.lower())

    def test_parse_tool_args_rejects_bad_json(self):
        args, error = agents.parse_tool_args("{room_id: 1203")
        self.assertEqual(args, {})
        self.assertIn("not valid JSON", error)

    def test_parse_tool_args_reads_an_object(self):
        args, error = agents.parse_tool_args('{"room_id": "1203"}')
        self.assertIsNone(error)
        self.assertEqual(args["room_id"], "1203")

    def test_run_tool_returns_clear_error_for_unknown_tool(self):
        self.assertIn("Unknown tool", agents.run_tool("nope", {}))


class TestMasking(HotelTestCase):
    def test_mask_identifier_keeps_last_four(self):
        self.assertEqual(agents.mask_identifier("CV-1203"), "***1203")
        self.assertEqual(agents.mask_identifier("1203"), "1203")

    def test_mask_text_hides_room_and_card(self):
        text = agents.mask_text("Room CV-1203, card 4111111111114242")
        self.assertNotIn("CV-1203", text)
        self.assertNotIn("4111111111114242", text)
        self.assertIn("1203", text)
        self.assertIn("4242", text)

    def test_mask_text_keeps_dates_and_amounts(self):
        text = agents.mask_text("Arrive 2026-12-25, total INR 4,200")
        self.assertEqual(text, "Arrive 2026-12-25, total INR 4,200")

    def test_contains_card_number(self):
        self.assertTrue(agents.contains_card_number("my card is 4111 1111 1111 4242"))
        self.assertFalse(agents.contains_card_number("room 1203 and 4242"))

    def test_get_balance_masks_the_reply(self):
        text = agents.get_balance("1203")
        self.assertIn("***1203", text)
        self.assertNotIn("4111111111114242", text)

    def test_tool_result_is_masked_before_it_reaches_the_model(self):
        result = agents.run_tool("get_balance", {"room_id": "CV-1203"})
        self.assertNotIn("CV-1203", result)
        self.assertNotIn("4111111111114242", result)


class TestConfirmation(HotelTestCase):
    def test_add_charge_is_cancelled_without_confirmation(self):
        before = len(agents.CHARGES["CV-1203"])

        with mock.patch.object(agents, "confirm_action", return_value=False):
            result = agents.add_charge("1203", "Test item", 100)

        self.assertIn("Cancelled", result)
        self.assertEqual(len(agents.CHARGES["CV-1203"]), before)

    def test_add_charge_runs_after_confirmation(self):
        before = len(agents.CHARGES["CV-1203"])

        with mock.patch.object(agents, "confirm_action", return_value=True):
            result = agents.add_charge("1203", "Test item", 100)

        self.assertIn("Added", result)
        self.assertEqual(len(agents.CHARGES["CV-1203"]), before + 1)
        self.assertTrue(os.path.exists(self.charge_log))

    def test_add_charge_rejects_bad_amount(self):
        with mock.patch.object(agents, "confirm_action", return_value=True):
            result = agents.add_charge("1203", "Test item", "lots")

        self.assertIn("must be a number", result)

    def test_checkout_is_cancelled_without_confirmation(self):
        with mock.patch.object(agents, "confirm_action", return_value=False):
            result = agents.checkout("1203")

        self.assertIn("Cancelled", result)
        self.assertFalse(agents.ROOMS["CV-1203"]["checked_out"])

    def test_checkout_runs_after_confirmation(self):
        with mock.patch.object(agents, "confirm_action", return_value=True):
            result = agents.checkout("1203")

        self.assertIn("checked out", result)
        self.assertTrue(agents.ROOMS["CV-1203"]["checked_out"])

    def test_execute_pending_action_adds_a_charge(self):
        result = agents.execute_pending_action(
            {"type": "add_charge", "room_id": "CV-1203", "item": "Late snack", "amount": 90}
        )
        self.assertIn("Added", result)


class TestToolLoop(HotelTestCase):
    def test_loop_stops_when_the_model_answers(self):
        calls = [
            reply(None, [tool_call("get_balance", '{"room_id": "1203"}')]),
            reply("Your balance is INR 4,670."),
        ]

        with mock.patch.object(agents, "chat", side_effect=calls):
            trace = []
            answer = agents.run_tool_loop(
                agents.BILL_SYSTEM_PROMPT,
                "What is my balance?",
                agents.bill_tools,
                trace=trace,
            )

        self.assertEqual(answer, "Your balance is INR 4,670.")
        self.assertEqual(trace[0]["name"], "get_balance")
        self.assertEqual(trace[0]["round"], 1)

    def test_loop_is_capped_at_five_rounds(self):
        def always_calls_tools(messages, tools=None, temperature=0.2, model=None):
            if tools:
                return reply(None, [tool_call("get_balance", '{"room_id": "1203"}')])
            return reply("Here is a summary from the bill.")

        with mock.patch.object(agents, "chat", side_effect=always_calls_tools) as fake:
            trace = []
            answer = agents.run_tool_loop(
                agents.BILL_SYSTEM_PROMPT,
                "Keep looking",
                agents.bill_tools,
                trace=trace,
            )

        self.assertEqual(answer, "Here is a summary from the bill.")
        self.assertEqual(fake.call_count, agents.MAX_TOOL_ROUNDS + 1)
        self.assertTrue(any(item["name"] == "loop_limit" for item in trace))
        tool_rounds = [item for item in trace if item["name"] == "get_balance"]
        self.assertEqual(len(tool_rounds), agents.MAX_TOOL_ROUNDS)

    def test_loop_returns_none_when_the_model_is_down(self):
        with mock.patch.object(agents, "chat", return_value=None):
            answer = agents.run_tool_loop(
                agents.BILL_SYSTEM_PROMPT,
                "Balance?",
                agents.bill_tools,
            )

        self.assertIsNone(answer)

    def test_loop_reports_cancellation_instead_of_the_model_claim(self):
        calls = [
            reply(None, [tool_call(
                "add_charge",
                '{"room_id": "1203", "item": "Test item", "amount": 100}',
            )]),
            reply("Done, I added the charge."),
        ]

        with mock.patch.object(agents, "chat", side_effect=calls), \
                mock.patch.object(agents, "confirm_action", return_value=False):
            answer = agents.run_tool_loop(
                agents.BILL_SYSTEM_PROMPT,
                "Add a test item.",
                agents.bill_tools,
            )

        self.assertIn("Cancelled", answer)
        self.assertNotIn("Done", answer)

    def test_loop_uses_parsed_arguments_and_reports_bad_json(self):
        calls = [
            reply(None, [tool_call("get_balance", "{bad json")]),
            reply("I could not read that."),
        ]

        with mock.patch.object(agents, "chat", side_effect=calls):
            trace = []
            agents.run_tool_loop(
                agents.BILL_SYSTEM_PROMPT,
                "Balance?",
                agents.bill_tools,
                trace=trace,
            )

        self.assertIn("not valid JSON", trace[0]["result"])


class TestJudgeAndScreener(HotelTestCase):
    def test_parse_judgement_clamps_score_and_fixes_verdict(self):
        result = agents.parse_judgement(
            {"score": 42, "verdict": "amazing", "strengths": ["clear"], "weaknesses": []}
        )
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["verdict"], "excellent")

    def test_parse_judgement_handles_garbage(self):
        result = agents.parse_judgement(None)
        self.assertIn("error", result)

    def test_judge_without_a_key_returns_an_error(self):
        with mock.patch.object(agents, "groq_client", None):
            result = agents.judge_answer("What is my balance?", "INR 4,670")

        self.assertIn("GROQ_API_KEY", result["error"])

    def test_parse_screen_result(self):
        result = agents.parse_screen_result(
            {
                "match_score": 140,
                "matched_skills": ["Python"],
                "missing_skills": ["Go"],
                "verdict": "odd",
                "summary": "Good fit.",
            }
        )
        self.assertEqual(result["match_score"], 100)
        self.assertEqual(result["verdict"], "strong")
        self.assertEqual(result["matched_skills"], ["Python"])

    def test_screen_resume_parses_json_from_the_model(self):
        payload = json.dumps(
            {
                "match_score": 72,
                "matched_skills": ["Python", "SQL"],
                "missing_skills": ["Airflow"],
                "verdict": "possible",
                "summary": "Close fit.",
            }
        )

        with mock.patch.object(agents, "chat", return_value=reply(payload)):
            result = agents.screen_resume("Resume text", "Job text")

        self.assertEqual(result["match_score"], 72)
        self.assertEqual(result["matched_skills"], ["Python", "SQL"])

    def test_screen_resume_needs_both_inputs(self):
        self.assertIn("resume", agents.screen_resume("", "Job")["error"].lower())
        self.assertIn("job", agents.screen_resume("Resume", "")["error"].lower())


class TestHandoffAndDashboard(HotelTestCase):
    def test_handoff_keywords(self):
        self.assertTrue(agents.wants_handoff("I want to talk to a manager"))
        self.assertFalse(agents.wants_handoff("What time is breakfast?"))

    def test_create_and_resolve_handoff(self):
        case = agents.create_handoff("Guest wants a manager about room CV-1203", "1203")

        self.assertEqual(case["status"], "open")
        self.assertEqual(case["room"], "***1203")
        self.assertNotIn("CV-1203", case["reason"])
        self.assertEqual(len(agents.open_handoffs()), 1)

        self.assertTrue(agents.resolve_handoff(case["id"]))
        self.assertEqual(agents.open_handoffs(), [])

    def test_usage_summary_counts_and_average(self):
        usage = agents.empty_usage()
        agents.record_usage(usage, "bill")
        agents.record_usage(usage, "bill")
        agents.record_usage(usage, "general")
        agents.record_judgement(usage, "Q1", {"score": 8, "verdict": "good", "summary": ""})
        agents.record_judgement(usage, "Q2", {"score": 6, "verdict": "fair", "summary": ""})

        summary = agents.usage_summary(usage)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_label"]["bill"], 2)
        self.assertEqual(summary["judged_count"], 2)
        self.assertEqual(summary["average_score"], 7.0)


class TestGuardrails(HotelTestCase):
    def test_rule_moderation_blocks_a_threat_without_a_model(self):
        with mock.patch.object(agents, "chat") as fake:
            check = agents.moderate("I will hurt you")

        self.assertFalse(check["allowed"])
        fake.assert_not_called()

    def test_empty_message_is_blocked(self):
        self.assertFalse(agents.moderate("   ")["allowed"])

    def test_agents_module_has_no_streamlit_import(self):
        with open(agents.__file__, encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("import streamlit", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
