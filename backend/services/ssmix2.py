"""
Service SS-MIX2 Bridge (Standardized Structured Medical Information eXchange 2)

Interface pour le standard japonais SS-MIX2 de stockage médical standardisé.
Parse les messages HL7 v2.5 (ADT, OML) au format japonais,
gère les chemins de stockage SS-MIX2 et les encodages CJK.

Fonctionne en mode mock par défaut (pas de dépendance externe requise).

Références:
    - SS-MIX2: https://www.jami.jp/english/
    - HL7 v2.5 JP Extension: http://www.hl7.jp/
    - Encodage: Shift_JIS (Windows-31J), ISO-2022-JP
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# SS-MIX2 data type codes
SSMIX2_DATA_TYPES = {
    "ADT": "ADT^A08",  # Patient demographics update
    "OML": "OML^O21",  # Laboratory/Pathology order
    "ORU": "ORU^R01",  # Observation result
    "ADT_A01": "ADT^A01",  # Admit/visit notification
    "ADT_A08": "ADT^A08",  # Update patient info
    "OML_O21": "OML^O21",  # Laboratory order
}

# HL7 v2.5 segment delimiters
HL7_FIELD_SEP = "|"
HL7_COMPONENT_SEP = "^"
HL7_REPEAT_SEP = "~"
HL7_ESCAPE_CHAR = "\\"
HL7_SUBCOMPONENT_SEP = "&"

# Supported encodings for Japanese medical systems
SUPPORTED_ENCODINGS = ["shift_jis", "iso-2022-jp", "utf-8", "euc-jp"]


def decode_japanese_text(data: bytes, encoding: str = "shift_jis") -> str:
    """Décode du texte japonais avec gestion des encodages médicaux.

    Tente le décodage avec l'encodage spécifié, puis avec les alternatives
    courantes dans les systèmes médicaux japonais.

    Args:
        data: Octets à décoder.
        encoding: Encodage préféré (shift_jis, iso-2022-jp, utf-8, euc-jp).

    Returns:
        Texte décodé en Unicode.
    """
    # Normaliser le nom d'encodage
    encoding_lower = encoding.lower().replace("-", "_").replace(" ", "_")
    if encoding_lower in ("shift_jis", "sjis", "windows_31j", "cp932"):
        encoding_lower = "shift_jis"
    elif encoding_lower in ("iso_2022_jp", "iso2022jp", "jis"):
        encoding_lower = "iso-2022-jp"

    # Essayer l'encodage demandé d'abord
    try_encodings = [encoding_lower] + [
        e for e in SUPPORTED_ENCODINGS if e != encoding_lower
    ]

    for enc in try_encodings:
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    # Dernier recours: UTF-8 avec remplacement
    return data.decode("utf-8", errors="replace")


def build_ssmix2_path(
    root: str,
    patient_id: str,
    order_date: str,
    data_type: str,
    message_id: str,
) -> str:
    """Construit un chemin de stockage SS-MIX2 standardisé.

    Format: {root}/{PatientID}/{OrderDate}/{DataType}/{MessageID}

    Args:
        root: Racine du stockage SS-MIX2.
        patient_id: Identifiant du patient.
        order_date: Date de la commande (format YYYYMMDD).
        data_type: Type de données (ADT, OML, etc.).
        message_id: Identifiant du message HL7.

    Returns:
        Chemin SS-MIX2 complet.
    """
    # Valider le format de date
    if not re.match(r"^\d{8}$", order_date):
        msg = f"Format de date invalide: {order_date} (attendu: YYYYMMDD)"
        raise ValueError(msg)

    path = PurePosixPath(root) / patient_id / order_date / data_type / message_id
    return str(path)


def parse_hl7_segment(segment_text: str) -> Dict[str, str]:
    """Parse un segment HL7 v2.5 en dictionnaire.

    Extrait les champs d'un segment HL7 en utilisant le séparateur standard.

    Args:
        segment_text: Texte du segment HL7 (ex: "PID|1|...|").

    Returns:
        Dictionnaire avec le type de segment et les champs indexés.
    """
    fields = segment_text.split(HL7_FIELD_SEP)
    segment_type = fields[0] if fields else ""
    result: Dict[str, str] = {"segment_type": segment_type}

    for i, field in enumerate(fields[1:], start=1):
        result[f"field_{i}"] = field

    return result


class SSMIX2Message:
    """Message HL7 v2.5 au format SS-MIX2.

    Parse et expose les données d'un message HL7 v2.5 conforme
    à l'extension japonaise SS-MIX2.

    Attributes:
        raw: Message brut.
        segments: Segments parsés.
        message_type: Type de message (ADT, OML, etc.).
        patient_id: Identifiant du patient.
        patient_name: Nom du patient (format japonais).
        order_date: Date de la commande.
    """

    def __init__(self, raw_message: str) -> None:
        self.raw = raw_message.strip()
        self.segments: List[Dict[str, str]] = []
        self.message_type: str = ""
        self.patient_id: str = ""
        self.patient_name: str = ""
        self.patient_name_kana: str = ""
        self.patient_dob: str = ""
        self.patient_gender: str = ""
        self.order_date: str = ""
        self.order_id: str = ""
        self.message_id: str = ""
        self._parse()

    def _parse(self) -> None:
        """Parse le message HL7 v2.5 brut."""
        lines = self.raw.split("\r")
        if not lines:
            lines = self.raw.split("\n")

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            segment = parse_hl7_segment(stripped)
            self.segments.append(segment)

            seg_type = segment.get("segment_type", "")

            if seg_type == "MSH":
                self._parse_msh(segment)
            elif seg_type == "PID":
                self._parse_pid(segment)
            elif seg_type == "OBR":
                self._parse_obr(segment)
            elif seg_type == "ORC":
                self._parse_orc(segment)

    def _parse_msh(self, segment: Dict[str, str]) -> None:
        """Parse le segment MSH (Message Header)."""
        # MSH-9: Message Type (field_8 car MSH-1 est le séparateur)
        msg_type = segment.get("field_8", "")
        self.message_type = msg_type.split(HL7_COMPONENT_SEP)[0] if msg_type else ""
        # MSH-10: Message Control ID
        self.message_id = segment.get("field_9", "")

    def _parse_pid(self, segment: Dict[str, str]) -> None:
        """Parse le segment PID (Patient Identification)."""
        # PID-3: Patient ID
        pid3 = segment.get("field_3", "")
        self.patient_id = pid3.split(HL7_COMPONENT_SEP)[0] if pid3 else ""

        # PID-5: Patient Name (JP format: Kanji^Kana)
        pid5 = segment.get("field_5", "")
        name_parts = pid5.split(HL7_COMPONENT_SEP)
        self.patient_name = name_parts[0] if name_parts else ""
        self.patient_name_kana = name_parts[1] if len(name_parts) > 1 else ""

        # PID-7: Date of Birth
        self.patient_dob = segment.get("field_7", "")

        # PID-8: Gender
        self.patient_gender = segment.get("field_8", "")

    def _parse_obr(self, segment: Dict[str, str]) -> None:
        """Parse le segment OBR (Observation Request)."""
        # OBR-7: Observation Date/Time
        obr7 = segment.get("field_7", "")
        if obr7 and len(obr7) >= 8:
            self.order_date = obr7[:8]

    def _parse_orc(self, segment: Dict[str, str]) -> None:
        """Parse le segment ORC (Common Order)."""
        # ORC-2: Placer Order Number
        orc2 = segment.get("field_2", "")
        self.order_id = orc2.split(HL7_COMPONENT_SEP)[0] if orc2 else ""

        # ORC-9: Date/Time of Transaction
        orc9 = segment.get("field_9", "")
        if orc9 and len(orc9) >= 8 and not self.order_date:
            self.order_date = orc9[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le message parsé en dictionnaire."""
        return {
            "messageType": self.message_type,
            "messageId": self.message_id,
            "patientId": self.patient_id,
            "patientName": self.patient_name,
            "patientNameKana": self.patient_name_kana,
            "patientDob": self.patient_dob,
            "patientGender": self.patient_gender,
            "orderDate": self.order_date,
            "orderId": self.order_id,
            "segmentCount": len(self.segments),
        }


class SSMIX2Service:
    """Service de pont SS-MIX2 pour l'intégration avec les systèmes japonais.

    Parse les messages HL7 v2.5 au format SS-MIX2, extrait les données
    démographiques et les informations de commande à partir de la structure
    de dossiers SS-MIX2.

    Fonctionne en mode mock par défaut pour le développement.

    Attributes:
        mock_mode: Si True, retourne des données de test déterministes.
        storage_root: Chemin racine du stockage SS-MIX2.
    """

    def __init__(
        self,
        storage_root: str = "/ssmix2/storage",
        mock_mode: bool = True,
    ) -> None:
        self.storage_root = storage_root
        self.mock_mode = mock_mode
        logger.info(
            "SSMIX2Service initialisé (mock_mode=%s, root=%s)",
            mock_mode,
            storage_root,
        )

    def parse_message(self, raw_message: str) -> SSMIX2Message:
        """Parse un message HL7 v2.5 SS-MIX2.

        Args:
            raw_message: Message HL7 brut.

        Returns:
            Message parsé avec les données extraites.
        """
        return SSMIX2Message(raw_message)

    def get_storage_path(
        self,
        patient_id: str,
        order_date: str,
        data_type: str,
        message_id: str,
    ) -> str:
        """Calcule le chemin de stockage SS-MIX2 pour un message.

        Args:
            patient_id: Identifiant du patient.
            order_date: Date de la commande (YYYYMMDD).
            data_type: Type de données SS-MIX2.
            message_id: Identifiant du message.

        Returns:
            Chemin complet SS-MIX2.
        """
        return build_ssmix2_path(
            root=self.storage_root,
            patient_id=patient_id,
            order_date=order_date,
            data_type=data_type,
            message_id=message_id,
        )

    def extract_from_path(self, path: str) -> Dict[str, str]:
        """Extrait les métadonnées depuis un chemin SS-MIX2.

        Le chemin doit suivre le format:
        {root}/{PatientID}/{OrderDate}/{DataType}/{MessageID}

        Args:
            path: Chemin SS-MIX2 complet.

        Returns:
            Dictionnaire avec PatientID, OrderDate, DataType, MessageID.
        """
        parts = PurePosixPath(path).parts
        if len(parts) < 4:
            msg = f"Chemin SS-MIX2 invalide (pas assez de segments): {path}"
            raise ValueError(msg)

        # Les 4 derniers segments sont: PatientID/OrderDate/DataType/MessageID
        return {
            "patientId": parts[-4],
            "orderDate": parts[-3],
            "dataType": parts[-2],
            "messageId": parts[-1],
        }

    def get_mock_adt_message(self) -> str:
        """Retourne un message ADT^A08 SS-MIX2 de test.

        Returns:
            Message HL7 v2.5 ADT brut pour les tests.
        """
        return (
            "MSH|^~\\&|HIS|HOSPITAL|||20240115103000||ADT^A08|MSG001|P|2.5||||||~ISOIR87\r"
            "EVN|A08|20240115103000\r"
            "PID|||PAT001^^^HOSPITAL||山田^太郎^^^^^L~ヤマダ^タロウ^^^^^P||19850315|M|||東京都新宿区1-1-1\r"
            "PV1||O|PATHOLOGY^^^HOSPITAL"
        )

    def get_mock_oml_message(self) -> str:
        """Retourne un message OML^O21 SS-MIX2 de test.

        Returns:
            Message HL7 v2.5 OML brut pour les tests.
        """
        return (
            "MSH|^~\\&|HIS|HOSPITAL|||20240115110000||OML^O21|MSG002|P|2.5||||||~ISOIR87\r"
            "PID|||PAT001^^^HOSPITAL||山田^太郎\r"
            "ORC|NW|ORD001^HIS||||||20240115110000\r"
            "OBR||ORD001^HIS||pathology^病理検査^L|||20240115110000"
        )

    def get_mock_patient_data(self) -> Dict[str, Any]:
        """Retourne des données patient SS-MIX2 déterministes pour les tests.

        Returns:
            Dictionnaire avec données démographiques et commandes.
        """
        adt = self.parse_message(self.get_mock_adt_message())
        oml = self.parse_message(self.get_mock_oml_message())

        return {
            "patient": adt.to_dict(),
            "order": oml.to_dict(),
            "storagePath": self.get_storage_path(
                patient_id="PAT001",
                order_date="20240115",
                data_type="ADT",
                message_id="MSG001",
            ),
        }

    def decode_text(self, data: bytes, encoding: str = "shift_jis") -> str:
        """Décode du texte avec gestion des encodages japonais.

        Args:
            data: Octets à décoder.
            encoding: Encodage source (shift_jis, iso-2022-jp, etc.).

        Returns:
            Texte décodé en Unicode.
        """
        return decode_japanese_text(data, encoding)

    def list_data_types(self) -> Dict[str, str]:
        """Retourne les types de données SS-MIX2 supportés.

        Returns:
            Dictionnaire code -> description des types de données.
        """
        return dict(SSMIX2_DATA_TYPES)
