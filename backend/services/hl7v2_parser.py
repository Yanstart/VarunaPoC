"""
HL7 v2 ORM/ORU Message Parser.

Parses HL7 v2.5 messages (ORM = Order, ORU = Result) from raw text.
Supports segments: MSH, PID, ORC, OBR, OBX, NTE.
Understands MLLP framing (0x0B header, 0x1C+0x0D trailer).

Mock mode: parse from string input, no network listener required.

References:
    - HL7 v2.5: https://www.hl7.org/implement/standards/product_brief.cfm?product_id=144
    - MLLP: Minimal Lower Layer Protocol (HL7 transport)
    - Field separator: |
    - Component separator: ^
"""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIELD_SEP = "|"
COMPONENT_SEP = "^"
REPEAT_SEP = "~"
ESCAPE_CHAR = "\\"
SUBCOMPONENT_SEP = "&"

# MLLP framing
MLLP_START = b"\x0b"  # Vertical Tab (0x0B)
MLLP_END = b"\x1c\x0d"  # File Separator + Carriage Return


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class HL7Segment(BaseModel):
    """Un segment HL7 v2 parse."""

    segment_type: str
    fields: list[str]
    raw: str


class PatientDemographics(BaseModel):
    """Donnees demographiques extraites du segment PID."""

    patient_id: str | None = None
    family_name: str | None = None
    given_name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    address: str | None = None
    phone: str | None = None
    ssn: str | None = None


class OrderInfo(BaseModel):
    """Informations de commande extraites des segments ORC/OBR."""

    order_control: str | None = None
    placer_order_number: str | None = None
    filler_order_number: str | None = None
    order_status: str | None = None
    universal_service_id: str | None = None
    observation_datetime: str | None = None
    ordering_provider: str | None = None
    result_status: str | None = None


class Observation(BaseModel):
    """Observation extraite du segment OBX."""

    set_id: str | None = None
    value_type: str | None = None
    observation_id: str | None = None
    observation_value: str | None = None
    units: str | None = None
    abnormal_flags: str | None = None
    observation_status: str | None = None


class HL7v2ParseResult(BaseModel):
    """Resultat complet du parsing d'un message HL7 v2."""

    message_type: str = Field(description="Type de message (ORM, ORU, ADT, etc.)")
    trigger_event: str = Field(default="", description="Evenement declencheur (O01, R01, etc.)")
    version: str = Field(default="2.5", description="Version HL7")
    sending_application: str = ""
    sending_facility: str = ""
    receiving_application: str = ""
    receiving_facility: str = ""
    message_datetime: str = ""
    message_control_id: str = ""
    segments: list[HL7Segment] = Field(default_factory=list)
    patient: PatientDemographics | None = None
    order: OrderInfo | None = None
    observations: list[Observation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# MLLP framing
# ---------------------------------------------------------------------------


def strip_mllp(data: bytes) -> str:
    """
    Retire le cadrage MLLP (0x0B ... 0x1C 0x0D) d'un message HL7.

    Args:
        data: Donnees brutes avec cadrage MLLP potentiel

    Returns:
        Message HL7 en texte sans cadrage MLLP
    """
    if data.startswith(MLLP_START):
        data = data[1:]
    if data.endswith(MLLP_END):
        data = data[:-2]
    return data.decode("utf-8", errors="replace").strip()


def add_mllp(message: str) -> bytes:
    """
    Ajoute le cadrage MLLP a un message HL7.

    Args:
        message: Message HL7 en texte

    Returns:
        Message avec cadrage MLLP (bytes)
    """
    return MLLP_START + message.encode("utf-8") + MLLP_END


# ---------------------------------------------------------------------------
# Segment parsers
# ---------------------------------------------------------------------------


def _get_field(fields: list[str], index: int, default: str = "") -> str:
    """Safely get a field by index."""
    if index < len(fields):
        return fields[index]
    return default


def _get_component(field: str, index: int, default: str = "") -> str:
    """Get a component from a field (0-based)."""
    parts = field.split(COMPONENT_SEP)
    if index < len(parts):
        return parts[index]
    return default


def _parse_msh(fields: list[str]) -> dict[str, str]:
    """Parse MSH (Message Header) segment.

    Field layout after splitting:
        fields[0] = "MSH"
        fields[1] = "|" (field separator, MSH-1)
        fields[2] = encoding characters (MSH-2, e.g. "^~\\&")
        fields[3] = sending application (MSH-3)
        fields[4] = sending facility (MSH-4)
        ...
        fields[9] = message type (MSH-9)
        fields[10] = message control ID (MSH-10)
        fields[11] = processing ID (MSH-11)
        fields[12] = version (MSH-12)
    """
    return {
        "sending_application": _get_field(fields, 3),
        "sending_facility": _get_field(fields, 4),
        "receiving_application": _get_field(fields, 5),
        "receiving_facility": _get_field(fields, 6),
        "message_datetime": _get_field(fields, 7),
        "message_type_raw": _get_field(fields, 9),
        "message_control_id": _get_field(fields, 10),
        "processing_id": _get_field(fields, 11),
        "version": _get_field(fields, 12),
    }


def _parse_pid(fields: list[str]) -> PatientDemographics:
    """Parse PID (Patient Identification) segment."""
    # PID-3: Patient Identifier List
    patient_id_field = _get_field(fields, 3)
    patient_id = _get_component(patient_id_field, 0) if patient_id_field else None

    # PID-5: Patient Name (Family^Given^Middle^Suffix^Prefix)
    name_field = _get_field(fields, 5)
    family_name = _get_component(name_field, 0) if name_field else None
    given_name = _get_component(name_field, 1) if name_field else None

    # PID-7: Date of Birth
    dob = _get_field(fields, 7) or None

    # PID-8: Administrative Sex
    gender = _get_field(fields, 8) or None

    # PID-11: Patient Address
    address_field = _get_field(fields, 11)
    address = _get_component(address_field, 0) if address_field else None

    # PID-13: Phone Number - Home
    phone = _get_field(fields, 13) or None

    # PID-19: SSN
    ssn = _get_field(fields, 19) or None

    return PatientDemographics(
        patient_id=patient_id,
        family_name=family_name,
        given_name=given_name,
        date_of_birth=dob,
        gender=gender,
        address=address,
        phone=phone,
        ssn=ssn,
    )


def _parse_orc(fields: list[str]) -> dict[str, str | None]:
    """Parse ORC (Common Order) segment."""
    return {
        "order_control": _get_field(fields, 1) or None,
        "placer_order_number": _get_field(fields, 2) or None,
        "filler_order_number": _get_field(fields, 3) or None,
        "order_status": _get_field(fields, 5) or None,
        "ordering_provider": _get_field(fields, 12) or None,
    }


def _parse_obr(fields: list[str]) -> dict[str, str | None]:
    """Parse OBR (Observation Request) segment."""
    return {
        "placer_order_number": _get_field(fields, 2) or None,
        "filler_order_number": _get_field(fields, 3) or None,
        "universal_service_id": _get_field(fields, 4) or None,
        "observation_datetime": _get_field(fields, 7) or None,
        "result_status": _get_field(fields, 25) or None,
    }


def _parse_obx(fields: list[str]) -> Observation:
    """Parse OBX (Observation/Result) segment."""
    return Observation(
        set_id=_get_field(fields, 1) or None,
        value_type=_get_field(fields, 2) or None,
        observation_id=_get_field(fields, 3) or None,
        observation_value=_get_field(fields, 5) or None,
        units=_get_field(fields, 6) or None,
        abnormal_flags=_get_field(fields, 8) or None,
        observation_status=_get_field(fields, 11) or None,
    )


def _parse_nte(fields: list[str]) -> str:
    """Parse NTE (Notes and Comments) segment."""
    return _get_field(fields, 3, "")


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------


class HL7v2Parser:
    """
    Parseur de messages HL7 v2.5 (ORM/ORU).

    Analyse les messages HL7 v2 a partir de texte brut.
    Supporte le decadrage MLLP automatique.
    """

    def parse(self, message: str | bytes) -> HL7v2ParseResult:
        """
        Parse un message HL7 v2.

        Accepte du texte brut ou des bytes avec cadrage MLLP.

        Args:
            message: Message HL7 v2 (str ou bytes avec MLLP)

        Returns:
            HL7v2ParseResult avec les donnees extraites
        """
        # Handle MLLP framing if bytes
        if isinstance(message, bytes):
            message = strip_mllp(message)

        # Normalize line endings
        message = message.replace("\r\n", "\r").replace("\n", "\r")
        lines = [line for line in message.split("\r") if line.strip()]

        if not lines:
            return HL7v2ParseResult(
                message_type="UNKNOWN",
                parse_errors=["Empty message"],
            )

        result = HL7v2ParseResult(message_type="UNKNOWN")
        segments: list[HL7Segment] = []
        observations: list[Observation] = []
        notes: list[str] = []
        order_data: dict[str, str | None] = {}

        for line in lines:
            self._parse_line(line, result, segments, observations, notes, order_data)

        result.segments = segments
        result.observations = observations
        result.notes = notes

        if order_data:
            result.order = OrderInfo(**order_data)

        return result

    def _parse_line(
        self,
        line: str,
        result: HL7v2ParseResult,
        segments: list[HL7Segment],
        observations: list[Observation],
        notes: list[str],
        order_data: dict[str, str | None],
    ) -> None:
        """Parse a single HL7 segment line and update result containers."""
        try:
            seg_type = line[:3]
            if seg_type == "MSH":
                fields = ["MSH", line[3], *line[4:].split(FIELD_SEP)]
            else:
                fields = line.split(FIELD_SEP)
                seg_type = fields[0] if fields else "UNK"

            segments.append(HL7Segment(segment_type=seg_type, fields=fields, raw=line))
            self._process_segment(seg_type, fields, result, observations, notes, order_data)
        except Exception as e:
            result.parse_errors.append(f"Error parsing segment: {e}")
            logger.warning("HL7 parse error on line: %s -> %s", line[:50], e)

    def _process_segment(
        self,
        seg_type: str,
        fields: list[str],
        result: HL7v2ParseResult,
        observations: list[Observation],
        notes: list[str],
        order_data: dict[str, str | None],
    ) -> None:
        """Dispatch segment to the appropriate parser."""
        if seg_type == "MSH":
            self._apply_msh(fields, result)
        elif seg_type == "PID":
            result.patient = _parse_pid(fields)
        elif seg_type == "ORC":
            order_data.update({k: v for k, v in _parse_orc(fields).items() if v})
        elif seg_type == "OBR":
            order_data.update({k: v for k, v in _parse_obr(fields).items() if v})
        elif seg_type == "OBX":
            observations.append(_parse_obx(fields))
        elif seg_type == "NTE":
            note_text = _parse_nte(fields)
            if note_text:
                notes.append(note_text)

    @staticmethod
    def _apply_msh(fields: list[str], result: HL7v2ParseResult) -> None:
        """Apply MSH header data to the parse result."""
        msh = _parse_msh(fields)
        result.sending_application = msh["sending_application"]
        result.sending_facility = msh["sending_facility"]
        result.receiving_application = msh["receiving_application"]
        result.receiving_facility = msh["receiving_facility"]
        result.message_datetime = msh["message_datetime"]
        result.message_control_id = msh["message_control_id"]
        result.version = msh.get("version", "2.5") or "2.5"

        msg_type_raw = msh["message_type_raw"]
        parts = msg_type_raw.split(COMPONENT_SEP)
        result.message_type = parts[0] if parts else "UNKNOWN"
        result.trigger_event = parts[1] if len(parts) > 1 else ""

    def build_ack(self, parse_result: HL7v2ParseResult, ack_code: str = "AA") -> str:
        """
        Construit un message ACK HL7 v2 pour un message recu.

        Args:
            parse_result: Resultat du parsing du message original
            ack_code: Code ACK (AA=accepted, AE=error, AR=rejected)

        Returns:
            Message ACK HL7 v2 en texte
        """
        now = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        ack_id = hashlib.sha256(
            f"{parse_result.message_control_id}{now}".encode()
        ).hexdigest()[:16]

        msh = (
            f"MSH|^~\\&|VarunaPoC|CHU_UCL_NAMUR|"
            f"{parse_result.sending_application}|"
            f"{parse_result.sending_facility}|"
            f"{now}||ACK^{parse_result.trigger_event}|{ack_id}|P|2.5"
        )
        msa = f"MSA|{ack_code}|{parse_result.message_control_id}"

        return f"{msh}\r{msa}"
