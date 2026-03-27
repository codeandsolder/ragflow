from unittest.mock import Mock, patch, AsyncMock
import pytest
from agent.component.categorize import Categorize, CategorizeParam
from api.db.services.llm_service import LLMBundle
from common.constants import LLMType


class TestCategorizeComponent:
    def setup_method(self):
        self.mock_canvas = Mock()
        self.mock_canvas.get_tenant_id.return_value = "test_tenant"
        self.mock_canvas.get_variable_value.return_value = ""
        self.mock_canvas.get_history.return_value = []

        self.param = CategorizeParam()
        self.categorize = Categorize(self.mock_canvas, "test_component", self.param)

        # Mock LLMBundle
        self.mock_llm_bundle = Mock(spec=LLMBundle)
        self.mock_llm_bundle.async_chat = AsyncMock()

        # Patch get_model_config_by_type_and_name
        self.get_model_config_patch = patch("api.db.joint_services.tenant_model_service.get_model_config_by_type_and_name")
        self.mock_get_model_config = self.get_model_config_patch.start()
        self.mock_get_model_config.return_value = {"id": "test_llm", "model_type": LLMType.CHAT.value}

        # Patch LLMBundle
        self.llm_bundle_patch = patch("agent.component.categorize.LLMBundle", return_value=self.mock_llm_bundle)
        self.llm_bundle_mock = self.llm_bundle_patch.start()

    def teardown_method(self):
        self.get_model_config_patch.stop()
        self.llm_bundle_patch.stop()

    def test_categorize_basic_classification(self):
        # Setup
        self.param.category_description = {
            "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
            "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
        }

        # Mock LLM response
        self.mock_llm_bundle.async_chat.return_value = "Question"

        # Test
        result = self.categorize._invoke(query="What is AI?")

        # Verify
        assert result["category_name"] == "Question"
        assert result["_next"] == ["next1"]
        self.mock_llm_bundle.async_chat.assert_called_once()

    def test_categorize_with_multiple_categories(self):
        # Setup
        self.param.category_description = {
            "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
            "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM response with multiple mentions
        self.mock_llm_bundle.async_chat.return_value = "This is a question about AI. It could be a Question or a Statement. I think it's a Question."

        # Test
        result = self.categorize._invoke(query="What is AI?")

        # Verify
        assert result["category_name"] == "Question"
        assert result["_next"] == ["next1"]

    def test_categorize_with_custom_prompt(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
        }
        self.param.query = "sys.query"

        # Mock LLM response
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        # Test
        result = self.categorize._invoke(query="How does neural network work?")

        # Verify
        assert result["category_name"] == "Technical"
        assert result["_next"] == ["next1"]

    def test_categorize_fallback_category(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM response that doesn't match any category
        self.mock_llm_bundle.async_chat.return_value = "This is a greeting message"

        # Test
        result = self.categorize._invoke(query="Hello")

        # Verify
        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_empty_input(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM response
        self.mock_llm_bundle.async_chat.return_value = "Other"

        # Test
        result = self.categorize._invoke(query="")

        # Verify
        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_invalid_output_handling(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM response that doesn't match any category
        self.mock_llm_bundle.async_chat.return_value = "This is a random text that doesn't match any category"

        # Test
        result = self.categorize._invoke(query="Hello")

        # Verify
        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_llm_failure_recovery(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM to raise exception
        self.mock_llm_bundle.async_chat.side_effect = Exception("LLM error")

        # Test
        with pytest.raises(Exception):
            self.categorize._invoke(query="What is AI?")

        # Verify error handling
        assert self.categorize.error() == "Task has been canceled" or self.categorize.error() == "LLM error"

    def test_categorize_message_history_window_size(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
        }
        self.param.message_history_window_size = 2
        self.mock_canvas.get_history.return_value = [{"role": "user", "content": "Previous question"}, {"role": "assistant", "content": "Previous answer"}]

        # Mock LLM response
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        # Test
        result = self.categorize._invoke(query="How does neural network work?")

        # Verify
        assert result["category_name"] == "Technical"
        assert result["_next"] == ["next1"]
        # Check that history was included in prompt
        self.mock_llm_bundle.async_chat.assert_called_once()
        call_args = self.mock_llm_bundle.async_chat.call_args[0]
        assert "Previous question" in call_args[1][0]["content"]
        assert "Previous answer" in call_args[1][1]["content"]

    def test_categorize_category_selection_logic(self):
        # Setup
        self.param.category_description = {
            "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
            "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
        }

        # Mock LLM response with multiple category mentions
        self.mock_llm_bundle.async_chat.return_value = "This is a Technical question about AI. It's also a General question."

        # Test
        result = self.categorize._invoke(query="How does neural network work?")

        # Verify
        # Should select the category with most mentions
        assert result["category_name"] in ["Technical", "General"]
        # Verify downstream
        assert result["_next"] in [["next1"], ["next2"]]

    def test_categorize_param_validation(self):
        # Test empty category_description
        with pytest.raises(ValueError, match=r"\[Categorize\] Category examples"):
            CategorizeParam().check()

        # Test empty category name
        param = CategorizeParam()
        param.category_description = {"": {"to": ["next1"], "examples": ["What is AI?"]}}
        with pytest.raises(ValueError, match=r"\[Categorize\] Category name can not be empty!"):
            param.check()

        # Test empty 'to' field
        param = CategorizeParam()
        param.category_description = {"Question": {"to": "", "examples": ["What is AI?"]}}
        with pytest.raises(ValueError, match=r"\[Categorize\] 'To' of category Question can not be empty!"):
            param.check()
