"""Unit tests for template_manager module."""
import json
import os
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTemplateManager:
    """Tests for the TemplateManager class."""

    def _make_manager(self, tmp_dir):
        """Create a TemplateManager that uses a temporary directory."""
        template_file = os.path.join(tmp_dir, "templates.json")
        with patch("template_manager.TEMPLATE_FILE", template_file), \
             patch("template_manager.ACCOUNTS_DIR", tmp_dir):
            from template_manager import TemplateManager
            mgr = TemplateManager()

            # Patch save to use tmp dir
            def patched_save():
                os.makedirs(tmp_dir, exist_ok=True)
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "templates": mgr.templates,
                        "updated_at": "2024-01-01T00:00:00"
                    }, f, ensure_ascii=False, indent=2)

            mgr._save_templates = patched_save
            return mgr

    def test_init_empty(self, tmp_path):
        """TemplateManager starts with empty templates when no file exists."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.templates == {}

    def test_add_template(self, tmp_path):
        """add_template creates a correctly structured template."""
        mgr = self._make_manager(str(tmp_path))
        result = mgr.add_template(
            template_id="greet1",
            name="Greeting",
            content="Hello {name}, welcome to {place}!",
            category="greetings"
        )

        assert result is True
        assert "greet1" in mgr.templates
        t = mgr.templates["greet1"]
        assert t["name"] == "Greeting"
        assert t["content"] == "Hello {name}, welcome to {place}!"
        assert t["category"] == "greetings"
        assert set(t["variables"]) == {"name", "place"}
        assert t["use_count"] == 0

    def test_add_template_auto_extracts_variables(self, tmp_path):
        """add_template auto-extracts variables from content."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Test", "Hi {user}, today is {day}")

        assert set(mgr.templates["t1"]["variables"]) == {"user", "day"}

    def test_add_template_with_explicit_variables(self, tmp_path):
        """add_template uses provided variables list instead of auto-extracting."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Test", "Hi {user}", variables=["user", "extra"])

        assert mgr.templates["t1"]["variables"] == ["user", "extra"]

    def test_get_template_existing(self, tmp_path):
        """get_template returns the template when it exists."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Test", "content")

        t = mgr.get_template("t1")
        assert t is not None
        assert t["name"] == "Test"
        assert t["template_id"] == "t1"

    def test_get_template_nonexistent(self, tmp_path):
        """get_template returns None for missing templates."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.get_template("nonexistent") is None

    def test_list_templates_empty(self, tmp_path):
        """list_templates returns empty list when no templates exist."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.list_templates() == []

    def test_list_templates_sorted_by_use_count(self, tmp_path):
        """list_templates returns templates sorted by use_count descending."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Low", "c1")
        mgr.add_template("t2", "High", "c2")
        mgr.templates["t2"]["use_count"] = 10
        mgr.templates["t1"]["use_count"] = 2

        templates = mgr.list_templates()
        assert templates[0]["name"] == "High"
        assert templates[1]["name"] == "Low"

    def test_list_templates_filter_by_category(self, tmp_path):
        """list_templates filters by category."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "A", "c", category="cat1")
        mgr.add_template("t2", "B", "c", category="cat2")
        mgr.add_template("t3", "C", "c", category="cat1")

        result = mgr.list_templates(category="cat1")
        assert len(result) == 2
        assert all(t["category"] == "cat1" for t in result)

    def test_delete_template_existing(self, tmp_path):
        """delete_template removes an existing template."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Test", "content")
        assert mgr.delete_template("t1") is True
        assert "t1" not in mgr.templates

    def test_delete_template_nonexistent(self, tmp_path):
        """delete_template returns False for missing templates."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.delete_template("nope") is False

    def test_render_template_simple(self, tmp_path):
        """render_template replaces variables correctly."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Greet", "Hello {name}, age {age}!")

        result = mgr.render_template("t1", name="Alice", age=30)
        assert result == "Hello Alice, age 30!"

    def test_render_template_missing_variable(self, tmp_path):
        """render_template replaces missing variables with empty string."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Greet", "Hello {name}!")

        result = mgr.render_template("t1")
        assert result == "Hello !"

    def test_render_template_increments_use_count(self, tmp_path):
        """render_template increments the use_count."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Test", "content")
        assert mgr.templates["t1"]["use_count"] == 0

        mgr.render_template("t1")
        assert mgr.templates["t1"]["use_count"] == 1

        mgr.render_template("t1")
        assert mgr.templates["t1"]["use_count"] == 2

    def test_render_template_nonexistent(self, tmp_path):
        """render_template returns None for missing templates."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.render_template("nope") is None

    def test_update_template(self, tmp_path):
        """update_template modifies fields correctly."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Old Name", "Old {content}", category="old_cat")

        result = mgr.update_template("t1", name="New Name", content="New {text}", category="new_cat")
        assert result is True
        t = mgr.templates["t1"]
        assert t["name"] == "New Name"
        assert t["content"] == "New {text}"
        assert t["category"] == "new_cat"
        assert t["variables"] == ["text"]

    def test_update_template_partial(self, tmp_path):
        """update_template only modifies provided fields."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Name", "Content {var}", category="cat")

        mgr.update_template("t1", name="New Name")
        t = mgr.templates["t1"]
        assert t["name"] == "New Name"
        assert t["content"] == "Content {var}"  # unchanged
        assert t["category"] == "cat"  # unchanged

    def test_update_template_nonexistent(self, tmp_path):
        """update_template returns False for missing templates."""
        mgr = self._make_manager(str(tmp_path))
        assert mgr.update_template("nope", name="x") is False

    def test_search_templates(self, tmp_path):
        """search_templates finds templates by keyword in name, content, or category."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Welcome Message", "Hello {name}", category="greetings")
        mgr.add_template("t2", "Goodbye", "Bye {name}", category="farewells")
        mgr.add_template("t3", "Promo", "Check our sale!", category="marketing")

        # Search by name
        results = mgr.search_templates("welcome")
        assert len(results) == 1
        assert results[0]["id"] == "t1"

        # Search by content
        results = mgr.search_templates("sale")
        assert len(results) == 1
        assert results[0]["id"] == "t3"

        # Search by category
        results = mgr.search_templates("farewell")
        assert len(results) == 1
        assert results[0]["id"] == "t2"

    def test_search_templates_case_insensitive(self, tmp_path):
        """search_templates is case-insensitive."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "Hello World", "content")

        results = mgr.search_templates("HELLO")
        assert len(results) == 1

    def test_get_categories(self, tmp_path):
        """get_categories returns sorted unique categories."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "A", "c", category="beta")
        mgr.add_template("t2", "B", "c", category="alpha")
        mgr.add_template("t3", "C", "c", category="beta")

        categories = mgr.get_categories()
        assert categories == ["alpha", "beta"]

    def test_get_stats(self, tmp_path):
        """get_stats returns aggregate statistics."""
        mgr = self._make_manager(str(tmp_path))
        mgr.add_template("t1", "A", "c", category="cat1")
        mgr.add_template("t2", "B", "c", category="cat1")
        mgr.add_template("t3", "C", "c", category="cat2")

        stats = mgr.get_stats()
        assert stats["total"] == 3
        assert stats["by_category"]["cat1"] == 2
        assert stats["by_category"]["cat2"] == 1
        assert len(stats["most_used"]) <= 5
        assert len(stats["recently_created"]) <= 5

    def test_load_from_existing_file(self, tmp_path):
        """TemplateManager loads templates from existing file."""
        template_file = os.path.join(str(tmp_path), "templates.json")
        data = {
            "templates": {
                "t1": {
                    "id": "t1",
                    "name": "Existing",
                    "content": "hello",
                    "category": "test",
                    "variables": [],
                    "use_count": 5
                }
            }
        }
        with open(template_file, 'w') as f:
            json.dump(data, f)

        with patch("template_manager.TEMPLATE_FILE", template_file), \
             patch("template_manager.ACCOUNTS_DIR", str(tmp_path)):
            from template_manager import TemplateManager
            mgr = TemplateManager()
            assert "t1" in mgr.templates
            assert mgr.templates["t1"]["use_count"] == 5

    def test_load_from_corrupted_file(self, tmp_path):
        """TemplateManager handles corrupted JSON gracefully."""
        template_file = os.path.join(str(tmp_path), "templates.json")
        with open(template_file, 'w') as f:
            f.write("not json!!!")

        with patch("template_manager.TEMPLATE_FILE", template_file), \
             patch("template_manager.ACCOUNTS_DIR", str(tmp_path)):
            from template_manager import TemplateManager
            mgr = TemplateManager()
            assert mgr.templates == {}
