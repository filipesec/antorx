import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class csv_helpers_tests(unittest.TestCase):
    def test_digits_only_removes_formatting_without_losing_zeroes(self):
        self.assertEqual(main.digits_only("DOC-0004-TEST"), "0004")
        self.assertEqual(main.digits_only(" 01 abc 23 "), "0123")
        self.assertEqual(main.digits_only(""), "")

    def test_read_passengers_uses_english_headers_and_preserves_zeroes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "passageiros.csv"
            csv_path.write_text(
                "original_order;name;document\n"
                "1;fictional passenger;001.234\n"
                "2;passenger without document;\n"
                "3;;999999\n",
                encoding="utf-8",
            )
            passengers = main.read_passengers(csv_path)
        self.assertEqual(len(passengers), 2)
        self.assertEqual(passengers[0]["name"], "fictional passenger")
        self.assertEqual(passengers[0]["document"], "001234")
        self.assertEqual(passengers[1]["document"], "")

    def test_read_passengers_accepts_legacy_portuguese_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "legacy.csv"
            csv_path.write_text(
                "ordem_original;nome;documento\n1;passageiro ficticio;001234\n",
                encoding="utf-8",
            )
            passengers = main.read_passengers(csv_path)
        self.assertEqual(passengers[0]["name"], "passageiro ficticio")
        self.assertEqual(passengers[0]["document"], "001234")

    def test_read_passengers_accepts_legacy_cpf_header(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "legacy.csv"
            csv_path.write_text("nome;cpf\npassageiro ficticio;001234\n", encoding="utf-8")
            passengers = main.read_passengers(csv_path)
        self.assertEqual(passengers[0]["document"], "001234")

    def test_missing_csv_raises_file_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.csv"
            with self.assertRaises(FileNotFoundError):
                main.read_passengers(missing_path)

    def test_example_has_no_automatically_submittable_document_numbers(self):
        passengers = main.read_passengers(main.default_csv)
        self.assertTrue(passengers)
        self.assertTrue(all(not passenger["document"] for passenger in passengers))


class issuer_field_tests(unittest.TestCase):
    class fake_element:
        def __init__(self):
            self.value = "old value"

        def clear(self):
            self.value = ""

        def send_keys(self, value):
            self.value += value

        def get_attribute(self, name):
            return self.value if name == "value" else None

    class fake_driver:
        def __init__(self):
            self.elements = {
                main.name_selector: issuer_field_tests.fake_element(),
                main.situation_selector: issuer_field_tests.fake_element(),
                main.document_type_selector: issuer_field_tests.fake_element(),
                main.document_number_selector: issuer_field_tests.fake_element(),
                main.issuer_selector: issuer_field_tests.fake_element(),
            }

        def find_element(self, by, selector):
            return self.elements[selector]

    class immediate_wait:
        def __init__(self, driver, timeout):
            self.driver = driver

        def until(self, condition):
            return condition(self.driver)

    class fake_select:
        def __init__(self, element):
            self.element = element

        def select_by_value(self, value):
            self.element.value = value

    def test_issuer_default_and_custom_values(self):
        for issuer in (None, "SSP", "SSP-PI", ""):
            driver = self.fake_driver()
            person = {"name": "fictional passenger", "document": "001234"}
            if issuer is not None:
                person["issuer"] = issuer
            with patch.object(main, "WebDriverWait", self.immediate_wait), patch.object(
                main, "Select", self.fake_select
            ):
                main.fill_current_form(driver, person)
            expected = main.default_issuer if issuer is None else issuer
            self.assertEqual(driver.elements[main.issuer_selector].value, expected)


class example_guard_tests(unittest.TestCase):
    def test_example_csv_is_blocked_from_submission(self):
        with patch("sys.argv", ["main.py"]):
            self.assertEqual(main.main(), 2)


if __name__ == "__main__":
    unittest.main()
