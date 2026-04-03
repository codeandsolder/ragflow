from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest
from api.db.services.llm_service import LLMBundle
from common.constants import LLMType

# Patch TenantLLMService.llm_id2llm_type at module level before importing Categorize
import api.db.services.tenant_llm_service

original_llm_id2llm_type = api.db.services.tenant_llm_service.TenantLLMService.llm_id2llm_type
api.db.services.tenant_llm_service.TenantLLMService.llm_id2llm_type = staticmethod(lambda x: LLMType.CHAT.value)

from agent.component.categorize import Categorize, CategorizeParam


class TestCategorizeComponent:
    def setup_method(self):
        self.mock_canvas = Mock()
        self.mock_canvas.get_tenant_id.return_value = "test_tenant"
        self.mock_canvas.get_variable_value.return_value = ""
        self.mock_canvas.get_history.return_value = []

        self.mock_llm_bundle = Mock(spec=LLMBundle)
        self.mock_llm_bundle.async_chat = AsyncMock()

        self.get_model_config_patch = patch(
            "agent.component.categorize.get_model_config_by_type_and_name",
            return_value={"id": "test_llm", "llm_name": "test_llm", "model_type": LLMType.CHAT.value, "llm_factory": "test_factory", "api_key": "test_key"},
        )
        self.get_model_config_patch.start()

        self.llm_bundle_patch = patch("agent.component.categorize.LLMBundle", return_value=self.mock_llm_bundle)
        self.llm_bundle_patch.start()

    def teardown_method(self):
        self.llm_bundle_patch.stop()
        self.get_model_config_patch.stop()

    def _create_categorize(self, category_description):
        """Helper to create Categorize instance with given categories."""
        param = CategorizeParam()
        param.llm_id = "test_llm"
        param.category_description = category_description
        return Categorize(self.mock_canvas, "test_component", param)

    def test_categorize_basic_classification(self):
        self.param = self._create_categorize(
            {
                "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
                "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "Question"

        result = self.param._invoke(query="What is AI?")

        assert result["category_name"] == "Question"
        assert result["_next"] == ["next1"]
        self.mock_llm_bundle.async_chat.assert_called_once()

    def test_categorize_with_multiple_categories(self):
        self.param = self._create_categorize(
            {
                "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
                "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a question about AI. It could be a Question or a Statement. I think it's a Question."

        result = self.param._invoke(query="What is AI?")

        assert result["category_name"] == "Question"
        assert result["_next"] == ["next1"]

    def test_categorize_with_custom_prompt(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            }
        )
        self.param.param.query = "sys.query"
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        result = self.param._invoke(query="How does neural network work?")

        assert result["category_name"] == "Technical"
        assert result["_next"] == ["next1"]

    def test_categorize_fallback_category(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a greeting message"

        result = self.param._invoke(query="Hello")

        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_empty_query(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "Other"

        result = self.param._invoke(query="")

        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_invalid_output_returns_fallback(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a random text that doesn't match any category"

        result = self.param._invoke(query="Hello")

        assert result["category_name"] == "Other"
        assert result["_next"] == ["next3"]

    def test_categorize_llm_failure_raises_exception(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.side_effect = Exception("LLM error")

        with pytest.raises(Exception):
            self.param._invoke(query="What is AI?")

    def test_categorize_message_history_window_size(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            }
        )
        self.param.param.message_history_window_size = 2
        self.mock_canvas.get_history.return_value = [{"role": "user", "content": "Previous question"}, {"role": "assistant", "content": "Previous answer"}]
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        result = self.param._invoke(query="How does neural network work?")

        assert result["category_name"] == "Technical"
        assert result["_next"] == ["next1"]
        self.mock_llm_bundle.async_chat.assert_called_once()
        call_args = self.mock_llm_bundle.async_chat.call_args[0]
        assert "Previous question" in call_args[1][0]["content"]
        assert "Previous answer" in call_args[1][1]["content"]

    def test_categorize_category_selection_logic(self):
        self.param = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a Technical question about AI. It's also a General question."

        result = self.param._invoke(query="How does neural network work?")

        assert result["category_name"] in ["Technical", "General"]
        assert result["_next"] in [["next1"], ["next2"]]

    def test_categorize_param_validation(self):
        with pytest.raises(ValueError, match=r"\[Categorize\] Category examples"):
            CategorizeParam().check()

        param = CategorizeParam()
        param.category_description = {"": {"to": ["next1"], "examples": ["What is AI?"]}}
        with pytest.raises(ValueError, match=r"\[Categorize\] Category name can not be empty!"):
            param.check()

        param = CategorizeParam()
        param.category_description = {"Question": {"to": "", "examples": ["What is AI?"]}}
        with pytest.raises(ValueError, match=r"\[Categorize\] 'To' of category Question can not be empty!"):
            param.check()
