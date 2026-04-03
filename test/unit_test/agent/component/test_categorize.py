from unittest.mock import Mock, patch, AsyncMock
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
        self.mock_canvas.is_canceled.return_value = False

        self.mock_llm_bundle = Mock(spec=LLMBundle)
        self.mock_llm_bundle.async_chat = AsyncMock()

        mock_config = {"id": "test_llm", "llm_name": "test_llm", "model_type": LLMType.CHAT.value, "llm_factory": "test_factory", "api_key": "test_key"}
        self.get_model_config_patch = patch(
            "agent.component.categorize.get_model_config_by_type_and_name",
            return_value=mock_config,
        )
        self.get_model_config_patch.start()

        self.get_model_config_llm_patch = patch(
            "agent.component.llm.get_model_config_by_type_and_name",
            return_value=mock_config,
        )
        self.get_model_config_llm_patch.start()

        self.llm_bundle_patch = patch("agent.component.categorize.LLMBundle", return_value=self.mock_llm_bundle)
        self.llm_bundle_patch.start()

        self.llm_bundle_llm_patch = patch("agent.component.llm.LLMBundle", return_value=self.mock_llm_bundle)
        self.llm_bundle_llm_patch.start()

    def teardown_method(self):
        self.llm_bundle_llm_patch.stop()
        self.llm_bundle_patch.stop()
        self.get_model_config_llm_patch.stop()
        self.get_model_config_patch.stop()

    def _create_categorize(self, category_description):
        """Helper to create Categorize instance with given categories."""
        param = CategorizeParam()
        param.llm_id = "test_llm"
        param.category_description = category_description
        return Categorize(self.mock_canvas, "test_component", param)

    def test_categorize_basic_classification(self):
        categorize = self._create_categorize(
            {
                "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
                "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "Question"

        categorize._invoke(query="What is AI?")

        assert categorize.output("category_name") == "Question"
        assert categorize.output("_next") == ["next1"]
        self.mock_llm_bundle.async_chat.assert_called_once()

    def test_categorize_with_multiple_categories(self):
        categorize = self._create_categorize(
            {
                "Question": {"description": "General question", "to": ["next1"], "examples": ["What is AI?"]},
                "Statement": {"description": "General statement", "to": ["next2"], "examples": ["AI is important"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a question about AI. It could be a Question or a Statement. I think it's a Question."

        categorize._invoke(query="What is AI?")

        assert categorize.output("category_name") == "Question"
        assert categorize.output("_next") == ["next1"]

    def test_categorize_with_custom_prompt(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            }
        )
        categorize._param.query = "sys.query"
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        categorize._invoke(query="How does neural network work?")

        assert categorize.output("category_name") == "Technical"
        assert categorize.output("_next") == ["next1"]

    def test_categorize_fallback_category(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a greeting message"

        categorize._invoke(query="Hello")

        assert categorize.output("category_name") == "Other"
        assert categorize.output("_next") == ["next3"]

    def test_categorize_empty_query(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "Other"

        categorize._invoke(query="")

        assert categorize.output("category_name") == "Other"
        assert categorize.output("_next") == ["next3"]

    def test_categorize_invalid_output_returns_fallback(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a random text that doesn't match any category"

        categorize._invoke(query="Hello")

        assert categorize.output("category_name") == "Other"
        assert categorize.output("_next") == ["next3"]

    def test_categorize_llm_failure_raises_exception(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.side_effect = Exception("LLM error")

        with pytest.raises(Exception):
            categorize._invoke(query="What is AI?")

    def test_categorize_message_history_window_size(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
            }
        )
        categorize._param.message_history_window_size = 2
        self.mock_canvas.get_history.return_value = [{"role": "user", "content": "Previous question"}, {"role": "assistant", "content": "Previous answer"}]
        self.mock_llm_bundle.async_chat.return_value = "Technical"

        categorize._invoke(query="How does neural network work?")

        assert categorize.output("category_name") == "Technical"
        assert categorize.output("_next") == ["next1"]
        self.mock_llm_bundle.async_chat.assert_called_once()
        call_args = self.mock_llm_bundle.async_chat.call_args[0]
        # History is formatted into the user_prompt (second positional arg, first message content)
        assert "Previous question" in call_args[1][0]["content"]

    def test_categorize_category_selection_logic(self):
        categorize = self._create_categorize(
            {
                "Technical": {"description": "Technical question", "to": ["next1"], "examples": ["How does neural network work?"]},
                "General": {"description": "General question", "to": ["next2"], "examples": ["What is AI?"]},
                "Other": {"description": "Other type", "to": ["next3"], "examples": ["Hello"]},
            }
        )
        self.mock_llm_bundle.async_chat.return_value = "This is a Technical question about AI. It's also a General question."

        categorize._invoke(query="How does neural network work?")

        assert categorize.output("category_name") in ["Technical", "General"]
        assert categorize.output("_next") in [["next1"], ["next2"]]

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
