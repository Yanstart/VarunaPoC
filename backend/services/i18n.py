"""
Service d'internationalisation (i18n)

Charge et sert les traductions pour l'interface multilingue.
Supporte le français (existant), l'anglais, le japonais, le chinois simplifié et le hindi.

Les traductions sont stockées en JSON et chargées au démarrage.

Locales supportées:
    - fr: Français (langue par défaut, existante)
    - en: English
    - ja: 日本語 (Japonais)
    - zh: 中文简体 (Chinois simplifié)
    - hi: हिन्दी (Hindi)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Locales supportées
SUPPORTED_LOCALES = ["fr", "en", "ja", "zh", "hi"]
DEFAULT_LOCALE = "fr"


# Traductions intégrées (fallback si les fichiers JSON ne sont pas disponibles)
_BUILTIN_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "fr": {
        "app.title": "VarunaPoC - Viewer de Pathologie Numérique",
        "app.subtitle": "Plateforme d'analyse de lames histologiques",
        "nav.home": "Accueil",
        "nav.viewer": "Visualiseur",
        "nav.compare": "Comparer",
        "nav.slides": "Lames",
        "nav.settings": "Paramètres",
        "nav.logout": "Déconnexion",
        "nav.login": "Connexion",
        "slide.loading": "Chargement de la lame...",
        "slide.loaded": "Lame chargée",
        "slide.error": "Erreur de chargement de la lame",
        "slide.notFound": "Lame non trouvée",
        "slide.select": "Sélectionner une lame",
        "slide.info": "Informations de la lame",
        "slide.format": "Format",
        "slide.dimensions": "Dimensions",
        "slide.magnification": "Grossissement",
        "slide.vendor": "Fabricant",
        "panel.annotations": "Annotations",
        "panel.layers": "Couches",
        "panel.ml": "Analyse IA",
        "panel.quality": "Qualité",
        "panel.detection": "Détection",
        "panel.clustering": "Regroupement",
        "panel.similarity": "Lames similaires",
        "panel.metadata": "Métadonnées",
        "btn.save": "Enregistrer",
        "btn.cancel": "Annuler",
        "btn.delete": "Supprimer",
        "btn.close": "Fermer",
        "btn.search": "Rechercher",
        "btn.filter": "Filtrer",
        "btn.export": "Exporter",
        "btn.analyze": "Analyser",
        "btn.confirm": "Confirmer",
        "btn.reject": "Rejeter",
        "error.generic": "Une erreur est survenue",
        "error.network": "Erreur de connexion au serveur",
        "error.unauthorized": "Accès non autorisé",
        "error.notFound": "Ressource non trouvée",
        "error.validation": "Erreur de validation",
        "search.placeholder": "Rechercher une lame...",
        "search.noResults": "Aucun résultat trouvé",
        "worklist.title": "Liste de travail",
        "worklist.pending": "En attente",
        "worklist.inProgress": "En cours",
        "worklist.completed": "Terminé",
        "folder.loading": "Chargement du dossier...",
        "folder.error": "Erreur lors du chargement du dossier",
        "folder.slides": "Lames détectées",
        "case.loading": "Chargement des cas...",
        "case.error": "Erreur lors du chargement des cas",
    },
    "en": {
        "app.title": "VarunaPoC - Digital Pathology Viewer",
        "app.subtitle": "Histological slide analysis platform",
        "nav.home": "Home",
        "nav.viewer": "Viewer",
        "nav.compare": "Compare",
        "nav.slides": "Slides",
        "nav.settings": "Settings",
        "nav.logout": "Logout",
        "nav.login": "Login",
        "slide.loading": "Loading slide...",
        "slide.loaded": "Slide loaded",
        "slide.error": "Slide loading error",
        "slide.notFound": "Slide not found",
        "slide.select": "Select a slide",
        "slide.info": "Slide information",
        "slide.format": "Format",
        "slide.dimensions": "Dimensions",
        "slide.magnification": "Magnification",
        "slide.vendor": "Vendor",
        "panel.annotations": "Annotations",
        "panel.layers": "Layers",
        "panel.ml": "AI Analysis",
        "panel.quality": "Quality",
        "panel.detection": "Detection",
        "panel.clustering": "Clustering",
        "panel.similarity": "Similar slides",
        "panel.metadata": "Metadata",
        "btn.save": "Save",
        "btn.cancel": "Cancel",
        "btn.delete": "Delete",
        "btn.close": "Close",
        "btn.search": "Search",
        "btn.filter": "Filter",
        "btn.export": "Export",
        "btn.analyze": "Analyze",
        "btn.confirm": "Confirm",
        "btn.reject": "Reject",
        "error.generic": "An error occurred",
        "error.network": "Server connection error",
        "error.unauthorized": "Unauthorized access",
        "error.notFound": "Resource not found",
        "error.validation": "Validation error",
        "search.placeholder": "Search for a slide...",
        "search.noResults": "No results found",
        "worklist.title": "Worklist",
        "worklist.pending": "Pending",
        "worklist.inProgress": "In progress",
        "worklist.completed": "Completed",
        "folder.loading": "Loading folder...",
        "folder.error": "Error loading folder",
        "folder.slides": "Detected slides",
        "case.loading": "Loading cases...",
        "case.error": "Error loading cases",
    },
    "ja": {
        "app.title": "VarunaPoC - デジタル病理ビューワー",
        "app.subtitle": "組織学的スライド分析プラットフォーム",
        "nav.home": "ホーム",
        "nav.viewer": "ビューワー",
        "nav.compare": "比較",
        "nav.slides": "スライド",
        "nav.settings": "設定",
        "nav.logout": "ログアウト",
        "nav.login": "ログイン",
        "slide.loading": "スライドを読み込み中...",
        "slide.loaded": "スライド読み込み完了",
        "slide.error": "スライド読み込みエラー",
        "slide.notFound": "スライドが見つかりません",
        "slide.select": "スライドを選択",
        "slide.info": "スライド情報",
        "slide.format": "フォーマット",
        "slide.dimensions": "寸法",
        "slide.magnification": "倍率",
        "slide.vendor": "メーカー",
        "panel.annotations": "アノテーション",
        "panel.layers": "レイヤー",
        "panel.ml": "AI分析",
        "panel.quality": "品質",
        "panel.detection": "検出",
        "panel.clustering": "クラスタリング",
        "panel.similarity": "類似スライド",
        "panel.metadata": "メタデータ",
        "btn.save": "保存",
        "btn.cancel": "キャンセル",
        "btn.delete": "削除",
        "btn.close": "閉じる",
        "btn.search": "検索",
        "btn.filter": "フィルター",
        "btn.export": "エクスポート",
        "btn.analyze": "分析",
        "btn.confirm": "確認",
        "btn.reject": "拒否",
        "error.generic": "エラーが発生しました",
        "error.network": "サーバー接続エラー",
        "error.unauthorized": "アクセスが拒否されました",
        "error.notFound": "リソースが見つかりません",
        "error.validation": "バリデーションエラー",
        "search.placeholder": "スライドを検索...",
        "search.noResults": "結果が見つかりません",
        "worklist.title": "ワークリスト",
        "worklist.pending": "保留中",
        "worklist.inProgress": "進行中",
        "worklist.completed": "完了",
        "folder.loading": "フォルダを読み込み中...",
        "folder.error": "フォルダの読み込みエラー",
        "folder.slides": "検出されたスライド",
        "case.loading": "症例を読み込み中...",
        "case.error": "症例の読み込みエラー",
    },
    "zh": {
        "app.title": "VarunaPoC - 数字病理查看器",
        "app.subtitle": "组织学切片分析平台",
        "nav.home": "首页",
        "nav.viewer": "查看器",
        "nav.compare": "对比",
        "nav.slides": "切片",
        "nav.settings": "设置",
        "nav.logout": "退出登录",
        "nav.login": "登录",
        "slide.loading": "正在加载切片...",
        "slide.loaded": "切片已加载",
        "slide.error": "切片加载错误",
        "slide.notFound": "未找到切片",
        "slide.select": "选择切片",
        "slide.info": "切片信息",
        "slide.format": "格式",
        "slide.dimensions": "尺寸",
        "slide.magnification": "放大倍率",
        "slide.vendor": "制造商",
        "panel.annotations": "标注",
        "panel.layers": "图层",
        "panel.ml": "AI分析",
        "panel.quality": "质量",
        "panel.detection": "检测",
        "panel.clustering": "聚类",
        "panel.similarity": "相似切片",
        "panel.metadata": "元数据",
        "btn.save": "保存",
        "btn.cancel": "取消",
        "btn.delete": "删除",
        "btn.close": "关闭",
        "btn.search": "搜索",
        "btn.filter": "筛选",
        "btn.export": "导出",
        "btn.analyze": "分析",
        "btn.confirm": "确认",
        "btn.reject": "拒绝",
        "error.generic": "发生错误",
        "error.network": "服务器连接错误",
        "error.unauthorized": "未授权访问",
        "error.notFound": "未找到资源",
        "error.validation": "验证错误",
        "search.placeholder": "搜索切片...",
        "search.noResults": "未找到结果",
        "worklist.title": "工作列表",
        "worklist.pending": "待处理",
        "worklist.inProgress": "进行中",
        "worklist.completed": "已完成",
        "folder.loading": "正在加载文件夹...",
        "folder.error": "文件夹加载错误",
        "folder.slides": "检测到的切片",
        "case.loading": "正在加载病例...",
        "case.error": "病例加载错误",
    },
    "hi": {
        "app.title": "VarunaPoC - डिजिटल पैथोलॉजी व्यूअर",
        "app.subtitle": "हिस्टोलॉजिकल स्लाइड विश्लेषण प्लेटफार्म",
        "nav.home": "होम",
        "nav.viewer": "व्यूअर",
        "nav.compare": "तुलना",
        "nav.slides": "स्लाइड",
        "nav.settings": "सेटिंग्स",
        "nav.logout": "लॉगआउट",
        "nav.login": "लॉगइन",
        "slide.loading": "स्लाइड लोड हो रही है...",
        "slide.loaded": "स्लाइड लोड हो गई",
        "slide.error": "स्लाइड लोडिंग त्रुटि",
        "slide.notFound": "स्लाइड नहीं मिली",
        "slide.select": "स्लाइड चुनें",
        "slide.info": "स्लाइड जानकारी",
        "slide.format": "प्रारूप",
        "slide.dimensions": "आयाम",
        "slide.magnification": "आवर्धन",
        "slide.vendor": "निर्माता",
        "panel.annotations": "एनोटेशन",
        "panel.layers": "परतें",
        "panel.ml": "AI विश्लेषण",
        "panel.quality": "गुणवत्ता",
        "panel.detection": "पहचान",
        "panel.clustering": "क्लस्टरिंग",
        "panel.similarity": "समान स्लाइड",
        "panel.metadata": "मेटाडेटा",
        "btn.save": "सहेजें",
        "btn.cancel": "रद्द करें",
        "btn.delete": "हटाएं",
        "btn.close": "बंद करें",
        "btn.search": "खोजें",
        "btn.filter": "फ़िल्टर",
        "btn.export": "निर्यात",
        "btn.analyze": "विश्लेषण",
        "btn.confirm": "पुष्टि करें",
        "btn.reject": "अस्वीकार करें",
        "error.generic": "एक त्रुटि हुई",
        "error.network": "सर्वर कनेक्शन त्रुटि",
        "error.unauthorized": "अनधिकृत पहुंच",
        "error.notFound": "संसाधन नहीं मिला",
        "error.validation": "सत्यापन त्रुटि",
        "search.placeholder": "स्लाइड खोजें...",
        "search.noResults": "कोई परिणाम नहीं मिला",
        "worklist.title": "कार्य सूची",
        "worklist.pending": "लंबित",
        "worklist.inProgress": "प्रगति में",
        "worklist.completed": "पूर्ण",
        "folder.loading": "फ़ोल्डर लोड हो रहा है...",
        "folder.error": "फ़ोल्डर लोडिंग त्रुटि",
        "folder.slides": "पहचानी गई स्लाइड",
        "case.loading": "केस लोड हो रहे हैं...",
        "case.error": "केस लोडिंग त्रुटि",
    },
}


class I18nService:
    """Service d'internationalisation pour le backend.

    Charge les traductions depuis des fichiers JSON ou utilise les traductions
    intégrées en fallback. Supporte 5 locales: fr, en, ja, zh, hi.

    Attributes:
        translations: Dictionnaire locale -> clé -> traduction.
        default_locale: Locale par défaut (fr).
    """

    def __init__(
        self,
        translations_dir: Optional[str] = None,
        default_locale: str = DEFAULT_LOCALE,
    ) -> None:
        self.default_locale = default_locale
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations(translations_dir)
        logger.info(
            "I18nService initialisé (%d locales chargées)",
            len(self.translations),
        )

    def _load_translations(self, translations_dir: Optional[str]) -> None:
        """Charge les traductions depuis le répertoire JSON ou les données intégrées."""
        # Charger d'abord les traductions intégrées
        for locale, trans in _BUILTIN_TRANSLATIONS.items():
            self.translations[locale] = dict(trans)

        # Puis surcharger avec les fichiers JSON si disponibles
        if translations_dir:
            dir_path = Path(translations_dir)
            if dir_path.is_dir():
                for locale in SUPPORTED_LOCALES:
                    json_file = dir_path / f"{locale}.json"
                    if json_file.exists():
                        try:
                            with json_file.open(encoding="utf-8") as f:
                                data = json.load(f)
                            self.translations[locale] = data
                            logger.info(
                                "Traductions chargées depuis %s (%d clés)",
                                json_file,
                                len(data),
                            )
                        except (json.JSONDecodeError, OSError) as e:
                            logger.warning(
                                "Erreur lors du chargement de %s: %s",
                                json_file,
                                e,
                            )

    def get_translations(self, locale: str) -> Dict[str, str]:
        """Retourne toutes les traductions pour une locale.

        Args:
            locale: Code de locale (fr, en, ja, zh, hi).

        Returns:
            Dictionnaire clé -> traduction. Fallback vers la locale par défaut.
        """
        if locale in self.translations:
            return self.translations[locale]

        # Fallback vers la locale par défaut
        logger.warning(
            "Locale non supportée: %s, fallback vers %s",
            locale,
            self.default_locale,
        )
        return self.translations.get(self.default_locale, {})

    def translate(self, key: str, locale: str = DEFAULT_LOCALE) -> str:
        """Traduit une clé dans la locale demandée.

        Args:
            key: Clé de traduction (ex: "nav.home").
            locale: Code de locale.

        Returns:
            Traduction ou la clé elle-même si non trouvée.
        """
        translations = self.translations.get(locale, {})
        if key in translations:
            return translations[key]

        # Fallback vers la locale par défaut
        default_translations = self.translations.get(self.default_locale, {})
        return default_translations.get(key, key)

    def get_supported_locales(self) -> List[Dict[str, str]]:
        """Retourne la liste des locales supportées avec leurs noms.

        Returns:
            Liste de dictionnaires avec code et nom de chaque locale.
        """
        locale_names = {
            "fr": "Français",
            "en": "English",
            "ja": "日本語",
            "zh": "中文简体",
            "hi": "हिन्दी",
        }
        return [
            {"code": code, "name": locale_names.get(code, code)}
            for code in SUPPORTED_LOCALES
            if code in self.translations
        ]

    def get_translation_count(self, locale: str) -> int:
        """Retourne le nombre de traductions pour une locale.

        Args:
            locale: Code de locale.

        Returns:
            Nombre de clés traduites.
        """
        return len(self.translations.get(locale, {}))

    def export_translations(self, locale: str) -> Dict[str, Any]:
        """Exporte les traductions d'une locale avec les métadonnées.

        Args:
            locale: Code de locale.

        Returns:
            Dictionnaire avec locale, nombre de clés et traductions.
        """
        translations = self.get_translations(locale)
        return {
            "locale": locale,
            "keyCount": len(translations),
            "translations": translations,
        }
