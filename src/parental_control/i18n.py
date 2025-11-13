#!/usr/bin/env python3
"""
Internationalization (i18n) support for Ubuntu Parental Control
Handles translations for blocked pages in Hebrew and English
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class I18n:
    """Internationalization handler for multi-language support"""

    # Supported languages
    SUPPORTED_LANGUAGES = ['he', 'en']
    DEFAULT_LANGUAGE = 'he'  # Hebrew is default (can be changed by admin)

    def __init__(self, locales_dir: Optional[Path] = None):
        """
        Initialize i18n system

        Args:
            locales_dir: Path to locales directory (defaults to project root/locales)
        """
        if locales_dir is None:
            # Default to project root/locales
            project_root = Path(__file__).parent.parent.parent
            locales_dir = project_root / 'locales'

        self.locales_dir = Path(locales_dir)
        self.translations: Dict[str, Dict] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files from locales directory"""
        for lang_code in self.SUPPORTED_LANGUAGES:
            locale_file = self.locales_dir / f'{lang_code}.json'

            if not locale_file.exists():
                logger.warning(f"Translation file not found: {locale_file}")
                continue

            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for: {lang_code}")
            except Exception as e:
                logger.error(f"Error loading translation file {locale_file}: {e}")

    def get_translation(self, lang_code: str, key_path: str, default: str = '') -> str:
        """
        Get translated string for given language and key path

        Args:
            lang_code: Language code ('he', 'en')
            key_path: Dot-separated path to translation key (e.g., 'common.app_name')
            default: Default value if translation not found

        Returns:
            Translated string or default value
        """
        # Validate language code
        if lang_code not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {lang_code}, falling back to {self.DEFAULT_LANGUAGE}")
            lang_code = self.DEFAULT_LANGUAGE

        # Get translations for language
        lang_translations = self.translations.get(lang_code, {})

        if not lang_translations:
            logger.warning(f"No translations loaded for language: {lang_code}")
            return default

        # Navigate through nested keys
        keys = key_path.split('.')
        current = lang_translations

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.debug(f"Translation key not found: {key_path} for language: {lang_code}")
                return default

        return str(current) if current is not None else default

    def get_all_translations(self, lang_code: str) -> Dict[str, Any]:
        """
        Get all translations for a specific language

        Args:
            lang_code: Language code ('he', 'en')

        Returns:
            Dictionary of all translations
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            lang_code = self.DEFAULT_LANGUAGE

        return self.translations.get(lang_code, {})

    def get_language_info(self, lang_code: str) -> Dict[str, str]:
        """
        Get language metadata (name, code, direction)

        Args:
            lang_code: Language code ('he', 'en')

        Returns:
            Dictionary with language_name, language_code, direction
        """
        translations = self.get_all_translations(lang_code)
        return {
            'language_name': translations.get('language_name', lang_code.upper()),
            'language_code': translations.get('language_code', lang_code),
            'direction': translations.get('direction', 'ltr')
        }

    def get_available_languages(self) -> list:
        """
        Get list of available languages with their metadata

        Returns:
            List of dicts with language info
        """
        languages = []
        for lang_code in self.SUPPORTED_LANGUAGES:
            info = self.get_language_info(lang_code)
            languages.append(info)
        return languages

    def flatten_translations(self, lang_code: str, prefix: str = '') -> Dict[str, str]:
        """
        Get flattened translations for use in templates

        Args:
            lang_code: Language code
            prefix: Prefix for keys (for nested access)

        Returns:
            Flat dictionary with dot-notation keys
        """
        translations = self.get_all_translations(lang_code)

        def flatten(d: dict, parent_key: str = '') -> dict:
            """Recursively flatten nested dictionary"""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        return flatten(translations, prefix)


# Global instance
_i18n_instance = None

def get_i18n() -> I18n:
    """Get global i18n instance (singleton)"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


# Flask template helper functions
def init_i18n_for_flask(app):
    """
    Initialize i18n for Flask application
    Adds template filters and context processors

    Args:
        app: Flask application instance
    """
    i18n = get_i18n()

    @app.template_filter('t')
    def translate_filter(key_path: str, lang: str = 'he') -> str:
        """
        Jinja2 filter for translations
        Usage: {{ 'common.app_name'|t('he') }}
        """
        return i18n.get_translation(lang, key_path, key_path)

    @app.context_processor
    def inject_i18n():
        """Inject i18n functions into all templates"""
        def t(key_path: str, lang: str = 'he') -> str:
            """Translation function for templates"""
            return i18n.get_translation(lang, key_path, key_path)

        def get_lang_info(lang_code: str) -> Dict[str, str]:
            """Get language info for templates"""
            return i18n.get_language_info(lang_code)

        def get_all_langs() -> list:
            """Get all available languages"""
            return i18n.get_available_languages()

        return dict(
            t=t,
            get_lang_info=get_lang_info,
            get_all_langs=get_all_langs
        )

    logger.info("i18n initialized for Flask")


if __name__ == '__main__':
    # Test the i18n system
    i18n = I18n()

    print("=== Testing i18n System ===")
    print(f"\nSupported languages: {i18n.SUPPORTED_LANGUAGES}")
    print(f"Default language: {i18n.DEFAULT_LANGUAGE}")

    print("\n=== Hebrew Translations ===")
    print(f"App Name (he): {i18n.get_translation('he', 'common.app_name')}")
    print(f"Tagline (he): {i18n.get_translation('he', 'common.tagline')}")
    print(f"Time Restricted Title (he): {i18n.get_translation('he', 'time_restricted.title')}")

    print("\n=== English Translations ===")
    print(f"App Name (en): {i18n.get_translation('en', 'common.app_name')}")
    print(f"Tagline (en): {i18n.get_translation('en', 'common.tagline')}")
    print(f"Time Restricted Title (en): {i18n.get_translation('en', 'time_restricted.title')}")

    print("\n=== Language Info ===")
    for lang in i18n.get_available_languages():
        print(f"{lang['language_name']} ({lang['language_code']}): direction={lang['direction']}")
