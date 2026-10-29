import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()

    def assert_clean(self):
        self.assertFalse(list(self.app.exception))

    def button(self, label):
        return next(element for element in self.app.button if element.label == label)

    def selectbox(self, label):
        return next(element for element in self.app.selectbox if element.label == label)

    def test_initial_render_and_operations(self):
        self.assert_clean()
        self.button("Run operation").click().run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["table"].count, 1)
        self.selectbox("Operation").select("Search").run()
        self.button("Run operation").click().run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["latest"].status, "Found")
        self.selectbox("Operation").select("Delete").run()
        self.button("Run operation").click().run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["table"].count, 0)

    def test_sample_switch_strategy_and_comparison(self):
        for strategy in ("Separate chaining", "Linear probing", "Double hashing"):
            self.selectbox("Collision strategy").select(strategy).run()
            self.button("Load collision sample").click().run()
            self.assert_clean()
            self.assertEqual(self.app.session_state["table"].count, 5)
            self.assertEqual(self.app.session_state["latest"].status, "Inserted")
            self.app.slider(key="trace_position").set_value(1).run()
            self.assert_clean()
        self.selectbox("Input distribution").select("Same initial bucket").run()
        next(element for element in self.app.slider if element.label == "Fill table to (%)").set_value(100).run()
        self.button("Run comparison").click().run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["comparison"][4], "Same initial bucket")
        self.assertEqual(self.app.session_state["comparison"][1][0]["Load factor"], 1)

    def test_reset_and_focused_interface(self):
        self.assertEqual([tab.label for tab in self.app.tabs], ["Simulator", "Compare strategies"])
        self.assertEqual(len(self.app.radio), 0)
        self.assertEqual(len(self.app.text_input), 0)
        self.assertEqual(self.selectbox("Operation").options, ["Insert", "Search", "Delete"])
        self.assertNotIn("comparison", self.app.session_state)
        self.button("Load collision sample").click().run()
        self.button("Clear table").click().run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["table"].count, 0)
        self.assertIsNone(self.app.session_state["latest"])
        self.assertEqual(self.app.session_state["collisions"], 0)
        self.button("Load collision sample").click().run()
        self.selectbox("Table size").select(7).run()
        self.assert_clean()
        self.assertEqual(self.app.session_state["table"].count, 0)



if __name__ == "__main__":
    unittest.main()
