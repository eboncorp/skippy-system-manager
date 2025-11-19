#!/usr/bin/env python3
"""
AI Classifier for Intelligent File Processor
Uses Claude via MCP for intelligent classification when enabled
"""

import logging
from typing import Dict, Any, Tuple, Optional
import json


class AIClassifier:
    """AI-powered classification using Claude via MCP"""

    def __init__(self, logger: logging.Logger, enabled: bool = False):
        """
        Initialize AI classifier

        Args:
            logger: Logger instance
            enabled: Whether AI classification is enabled
        """
        self.logger = logger
        self.enabled = enabled
        self.available = False

        if self.enabled:
            self.available = self._check_mcp_availability()

    def _check_mcp_availability(self) -> bool:
        """Check if MCP/Claude API is available"""
        try:
            # Try to import anthropic
            import anthropic
            self.logger.info("Claude AI classification is available")
            return True
        except ImportError:
            self.logger.warning("Claude AI not available - install with: pip install anthropic")
            return False

    def is_available(self) -> bool:
        """Check if AI classification is available"""
        return self.enabled and self.available

    def classify(self, analysis: Dict[str, Any], rule_based_result: Tuple[str, int, Dict] = None) -> Tuple[Optional[str], Optional[int], Dict]:
        """
        Classify using AI

        Args:
            analysis: Content analysis result
            rule_based_result: Optional result from rule-based classifier

        Returns:
            Tuple of (category, confidence, metadata) or (None, None, {}) if not available
        """
        if not self.is_available():
            return None, None, {}

        try:
            # Prepare content for AI
            text_content = analysis.get('text_content', '')[:2000]  # Limit to 2000 chars
            filename = analysis.get('name', '')
            metadata = analysis.get('metadata', {})

            # Build prompt
            prompt = self._build_classification_prompt(filename, text_content, metadata, rule_based_result)

            # Call Claude
            response = self._call_claude(prompt)

            if response:
                category, confidence = self._parse_response(response)
                return category, confidence, {
                    'method': 'ai_classification',
                    'model': 'claude',
                    'rule_based_suggestion': rule_based_result[0] if rule_based_result else None
                }

        except Exception as e:
            self.logger.error(f"AI classification error: {e}")

        return None, None, {}

    def _build_classification_prompt(self, filename: str, text_content: str,
                                     metadata: Dict, rule_based_result: Tuple = None) -> str:
        """Build classification prompt for Claude"""

        prompt = f"""Classify this file into one of these categories:
- campaign: RunDaveRun political campaign materials (Dave Biggers for Louisville Metro Council)
- business: Business documents (invoices, contracts, receipts, proposals)
- personal: Personal documents (medical, financial, legal, insurance)
- technical: Code, scripts, documentation, configs
- media: Photos, videos, audio files

Filename: {filename}

"""

        if text_content:
            prompt += f"Content preview:\n{text_content}\n\n"

        if metadata:
            prompt += f"Metadata: {json.dumps(metadata, indent=2)}\n\n"

        if rule_based_result:
            category, confidence, _ = rule_based_result
            prompt += f"Rule-based suggestion: {category} ({confidence}% confidence)\n\n"

        prompt += """Respond with ONLY a JSON object in this format:
{
  "category": "campaign|business|personal|technical|media",
  "confidence": 0-100,
  "reasoning": "brief explanation"
}"""

        return prompt

    def _call_claude(self, prompt: str) -> Optional[str]:
        """
        Call Claude API

        Args:
            prompt: Classification prompt

        Returns:
            Claude's response text or None
        """
        try:
            import anthropic
            import os

            # Get API key from environment
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                self.logger.error("ANTHROPIC_API_KEY not set in environment")
                return None

            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            return message.content[0].text

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            return None

    def _parse_response(self, response: str) -> Tuple[str, int]:
        """
        Parse Claude's JSON response

        Args:
            response: Raw response from Claude

        Returns:
            Tuple of (category, confidence)
        """
        try:
            # Extract JSON from response
            # Claude might add explanation before/after JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group())
                category = data.get('category', 'unknown')
                confidence = int(data.get('confidence', 50))

                self.logger.info(f"AI classified as: {category} ({confidence}%)")
                if 'reasoning' in data:
                    self.logger.debug(f"  Reasoning: {data['reasoning']}")

                return category, confidence

        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")

        return 'unknown', 50


if __name__ == "__main__":
    # Test AI classifier
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Check if enabled
    import os
    enabled = bool(os.getenv('ANTHROPIC_API_KEY'))

    ai = AIClassifier(logger, enabled=enabled)

    if ai.is_available():
        print("✅ AI Classification is available\n")

        # Test classification
        test_analysis = {
            'name': 'invoice_amazon.pdf',
            'text_content': 'INVOICE\nAmazon.com\nOrder #123\nTotal: $45.99',
            'metadata': {}
        }

        category, confidence, meta = ai.classify(test_analysis)

        if category:
            print(f"Classification: {category}")
            print(f"Confidence: {confidence}%")
            print(f"Method: {meta['method']}")
        else:
            print("Classification failed")

    else:
        print("❌ AI Classification not available")
        if not enabled:
            print("\nTo enable:")
            print("  export ANTHROPIC_API_KEY='your-api-key'")
            print("  pip install anthropic")
