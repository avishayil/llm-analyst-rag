from src.prompts.vulnerability_trend_analysis_prompt import (
    VulnerabilityTrendAnalysisPrompt,
)


def test_vulnerability_patch_prompt_builder():
    """Test the prompt builder for the VulnerabilityPatchPrompt."""
    prompt = VulnerabilityTrendAnalysisPrompt().prompt_builder(
        criteria="Apache",
    )
    assert "Apache" in prompt.template
    assert "<output>" in prompt.template
    assert "<trend>\n                <summary>" in prompt.template
