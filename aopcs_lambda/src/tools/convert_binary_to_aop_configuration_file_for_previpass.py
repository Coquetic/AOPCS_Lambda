from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Any, Dict, List, Optional
import requests
import binascii
from enum import Enum
import pytz

from aws_lambda_powertools import Logger

from aopcs_lambda.src.models.metadata_model import AOPCSMetadataModel

logger = Logger()


# Enum for payloadType
class PayloadType(Enum):
    ARGOS_3 = "000"
    ARGOS_NEO = "001"
    ARGOS_4 = "010"
    KINEIS_V1 = "011"
    SPARE_1 = "100"
    SPARE_2 = "101"
    SPARE_3 = "110"
    SPARE_4 = "111"


# Enum for formatReference
class FormatReference(Enum):
    AOP_MONOSAT = 0x0000026C
    AOP_MULTISAT = 0x0000035A
    CS_2_SAT = 0x00000443
    CS_10_SAT = 0x00000575
    CS_17_SAT = 0x0000062F


# Satellite identification table (Satellite Address (hexadecimal coding) : Satellite Mnemonic)
satellite_identification = {
    "FC": "NP",
    "F9": "MB",
    "FD": "SR",
    "FB": "MC",
    "F2": "O3",
    "F1": "CS",
    "F3": "MD",
    "F4": "ME",
    "B": "1A",
    "16": "1B",
    "1D": "1C",
    "27": "1D",
    "2C": "1E",
    "31": "2A",
    "3A": "2B",
    "45": "2C",
    "4E": "2D",
    "53": "2E",
    "58": "3A",
    "62": "3B",
    "69": "3C",
    "74": "3D",
    "7F": "3E",
    "81": "4A",
    "8A": "4B",
    "97": "4C",
    "9C": "4D",
    "A6": "4E",
    "AD": "5A",
    "B0": "5B",
    "BB": "5C",
    "C4": "5D",
    "CF": "5E",
}

downlink_status = {"OFF": 0, "ARGOS_2": 0, "ARGOS_3": 3, "ARGOS_4": 4, "ARGOS_NEO": 0, "KINEIS_V1": 6}

uplink_status = {"OFF": 0, "ARGOS_2": 2, "ARGOS_3": 3, "ARGOS_4": 4, "ARGOS_NEO": 5, "KINEIS_V1": 6}


# Function to make the API call and fetch binary data
def fetch_binary_data(api_url: str, headers: dict[str, str]) -> bytes:
    response = requests.get(api_url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")


# Function to read binary data from a file
def read_binary_data_from_file(file_path: str) -> bytes:
    with open(file_path, "rb") as file:
        return file.read()


# Function to convert binary data to hexadecimal
def binary_to_hex(binary_data: bytes) -> str:
    return binascii.hexlify(binary_data).decode("utf-8")


# Function to convert hexadecimal data to bits
def hex_to_bits(hex_data: str) -> str:
    return bin(int(hex_data, 16))[2:].zfill(len(hex_data) * 4)


# Types for JSON-like returns
ParsedData = Dict[Any, Any]


# Function to parse binary data
def parse_binary_data(binary_data: bytes) -> List[ParsedData]:
    hex_data = binary_to_hex(binary_data)
    bit_data = hex_to_bits(hex_data)
    parsed_data = []
    index = 0

    while index < len(bit_data):
        # broadcaster_reference = int(bit_data[index : index + 8], 2)
        format_reference = int(bit_data[index + 8 : index + 40], 2)

        if format_reference == FormatReference.AOP_MULTISAT.value:
            parsed_data.append(parse_aop_multisat(bit_data, index))
        elif format_reference == FormatReference.AOP_MONOSAT.value:
            parsed_data.append(parse_aop_monosat(bit_data, index))
        elif format_reference in [FormatReference.CS_2_SAT.value, FormatReference.CS_10_SAT.value, FormatReference.CS_17_SAT.value]:
            parsed_data.append(parse_constellation_status(bit_data, index, format_reference))
        else:
            raise Exception(f"Unknown format reference: {format_reference}")

        index += get_format_size_in_bits(format_reference)

    return parsed_data


# Function to parse AOP Multisat format
def parse_aop_multisat(bit_data: str, index: int) -> ParsedData:
    aop_multisat: ParsedData = {}
    aop_multisat["broadcasterReference"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    aop_multisat["formatReference"] = FormatReference(int(bit_data[index : index + 32], 2)).name
    index += 32
    aop_multisat["satelliteReference"] = parse_aop_satellite_data(bit_data, index)
    index += 141
    aop_multisat["relativeSatellites"] = [parse_aop_relative_satellite(bit_data, index + i * 25) for i in range(4)]
    index += 100
    aop_multisat["frameCheckSequence"] = int(bit_data[index : index + 16], 2)
    index += 16
    return aop_multisat


# Function to parse AOP Monosat format
def parse_aop_monosat(bit_data: str, index: int) -> ParsedData:
    aop_monosat: ParsedData = {}
    aop_monosat["broadcasterReference"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    aop_monosat["formatReference"] = FormatReference(int(bit_data[index : index + 32], 2)).name
    index += 32
    aop_monosat["satelliteData"] = parse_aop_satellite_data(bit_data, index)
    index += 141
    index += 1  # zeroPadding1
    aop_monosat["frameCheckSequence"] = int(bit_data[index : index + 16], 2)
    index += 16
    return aop_monosat


# Function to parse Constellation Status format
def parse_constellation_status(bit_data: str, index: int, format_reference: int) -> ParsedData:
    constellation_status: ParsedData = {}
    constellation_status["broadcasterReference"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    constellation_status["formatReference"] = FormatReference(int(bit_data[index : index + 32], 2)).name
    index += 32
    constellation_status["counter"] = int(bit_data[index : index + 6], 2)
    index += 6
    constellation_status["index"] = int(bit_data[index : index + 3], 2)
    index += 3
    constellation_status["totalNumberOfMessages"] = int(bit_data[index : index + 3], 2)
    index += 3
    num_satellites = {0x00000443: 2, 0x00000575: 10, 0x0000062F: 17}[format_reference]
    constellation_status["satellitesStatus"] = [parse_satellite_status(bit_data, index + i * 13) for i in range(num_satellites)]
    index += 13 * num_satellites
    index += 5 if format_reference == 0x00000443 else 0  # zeroPaddingN
    constellation_status["fcs"] = int(bit_data[index : index + 16], 2)
    index += 16
    return constellation_status


# Function to parse satellite data
def parse_aop_satellite_data(bit_data: str, index: int) -> ParsedData:
    satellite_data: ParsedData = {}
    satellite_data["satelliteAddress"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    date_bits = bit_data[index : index + 35]
    date_value = int(date_bits, 2) * 0.125  # Convert to seconds with a precision of 0.125
    offset_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    satellite_data["date"] = (offset_date + timedelta(seconds=date_value)).isoformat(timespec="milliseconds")
    index += 35
    satellite_data["anLongitude"] = int(bit_data[index : index + 19], 2) * 0.001
    index += 19
    satellite_data["anLongitudeDrift"] = -28.000 + int(bit_data[index : index + 13], 2) * 0.001
    index += 13
    satellite_data["nodalPeriod"] = 84.4890 + int(bit_data[index : index + 18], 2) * 0.0001
    index += 18
    satellite_data["semiMajorAxis"] = 6378137 + int(bit_data[index : index + 20], 2)
    index += 20
    satellite_data["semiMajorAxisDecay"] = int(bit_data[index : index + 10], 2) * 0.1
    index += 10
    satellite_data["inclination"] = int(bit_data[index : index + 18], 2) * 0.001
    return satellite_data


# Function to parse relative satellite data
def parse_aop_relative_satellite(bit_data: str, index: int) -> ParsedData:
    relative_satellite: ParsedData = {}
    relative_satellite["satelliteAddressRelative"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    relative_satellite["deltaDateRelative"] = -8200 + int(bit_data[index : index + 17], 2) * 0.125
    return relative_satellite


# Function to parse satellite status
def parse_satellite_status(bit_data: str, index: int) -> ParsedData:
    satellite_status: ParsedData = {}
    satellite_status["satelliteAddress"] = f"{int(bit_data[index : index + 8], 2):X}"
    index += 8
    payload_type_bits = bit_data[index : index + 3]
    satellite_status["payloadType"] = PayloadType(payload_type_bits).name
    index += 3
    satellite_status["payloadUplinkMissionStatus"] = bool(int(bit_data[index : index + 1], 2))
    index += 1
    satellite_status["payloadDownlinkMissionStatus"] = bool(int(bit_data[index : index + 1], 2))
    return satellite_status


# Function to get the format size in bits
def get_format_size_in_bits(format_reference: int) -> int:
    if format_reference == FormatReference.AOP_MULTISAT.value:
        return 297 + 7
    elif format_reference == FormatReference.AOP_MONOSAT.value:
        return 198 + 2
    elif format_reference == FormatReference.CS_2_SAT.value:
        return 99 + 5
    elif format_reference == FormatReference.CS_10_SAT.value:
        return 198 + 2
    elif format_reference == FormatReference.CS_17_SAT.value:
        return 297 + 7
    else:
        raise Exception(f"Unknown format reference: {format_reference}")


# Functions to bulid metadata from CSV Rows
def build_metadata_from_csv_rows(rows: List[Dict[str, Any]]) -> Optional[AOPCSMetadataModel]:
    """Construit la metadata (dates min/max) à partir des lignes CSV déjà prêtes."""
    if not rows:
        return AOPCSMetadataModel()

    dates = [
        datetime(
            int(row["year"]),
            int(row["month"]),
            int(row["day"]),
            int(row["hour"]),
            int(row["minute"]),
            int(row["second"]),
            tzinfo=timezone.utc,
        )
        for row in rows
    ]

    min_date = min(dates)
    max_date = max(dates)

    metadata = AOPCSMetadataModel(
        satellite_prevision_min_date=min_date,
        satellite_prevision_max_date=max_date,
    )

    logger.info(f"Generated metadata from CSV: min={min_date}, max={max_date}")
    return metadata


# Functions to convert parsed data to CSV format
def build_csv_row(address: str, date: datetime, data: Dict[str, Any], name: str, down_status: str = "", up_status: str = "") -> Dict[str, Any]:
    return {
        "satName": name,
        "satHexId": address,
        "satDcsId": "0",
        "downlinkStatus": down_status,
        "uplinkStatus": up_status,
        "year": date.strftime("%Y"),
        "month": date.strftime("%m"),
        "day": date.strftime("%d"),
        "hour": date.strftime("%H"),
        "minute": date.strftime("%M"),
        "second": date.strftime("%S"),
        "semiMajorAxisKm": f"{data['semiMajorAxis'] * 0.001:>9.3f}",
        "inclinationDeg": f"{data['inclination']:>8.4f}",
        "ascNodeLongitudeDeg": format(data["ascNodeLongitudeDeg"], ">8.3f"),  # Ascending node longitude (not available in relative satellites)
        "ascNodeDriftDeg": f"{data['anLongitudeDrift']:>8.3f}",
        "orbitPeriodMin": f"{data['nodalPeriod']:>9.4f}",
        "semiMajorAxisDriftMeterPerDay": f"{data['semiMajorAxisDecay']:>6.2f}",
    }


def convert_to_csv(parsed_data: List[ParsedData], csv_file_path: Optional[str] = None, satellite_whitelist: List[str] = []) -> Any:
    fieldnames = [
        "satName",
        "satHexId",
        "satDcsId",
        "downlinkStatus",
        "uplinkStatus",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "semiMajorAxisKm",
        "inclinationDeg",
        "ascNodeLongitudeDeg",
        "ascNodeDriftDeg",
        "orbitPeriodMin",
        "semiMajorAxisDriftMeterPerDay",
    ]

    satellite_data_map = {}

    for entry in parsed_data:
        if "satelliteData" in entry or "satelliteReference" in entry:
            key = "satelliteData" if "satelliteData" in entry else "satelliteReference"
            sat_data = entry[key]
            address = sat_data["satelliteAddress"]

            name = satellite_identification.get(address)
            if not name:
                continue
            sat_data["ascNodeLongitudeDeg"] = sat_data["anLongitude"]

            satellite_data_map[address] = build_csv_row(address[0], datetime.fromisoformat(sat_data["date"]), sat_data, name)

            # Relative satellites (only for AOP_MULTISAT)
            for rel_sat in entry.get("relativeSatellites", []):
                rel_address = rel_sat["satelliteAddressRelative"]
                rel_name = satellite_identification.get(rel_address)
                if not rel_name:
                    continue
                # delta = timedelta(seconds=rel_sat["deltaDateRelative"] * 0.125)
                # rel_date = (datetime.fromisoformat(sat_data["date"]) + delta).isoformat()
                reference_bulletin = datetime.fromisoformat(sat_data["date"])
                rel_date = reference_bulletin + timedelta(seconds=rel_sat["deltaDateRelative"])

                driftCoefficient = (sat_data["anLongitudeDrift"] / sat_data["nodalPeriod"]) / 0.001 / 60 * 0.125
                ascNodeLongitudeDeg = float(sat_data["anLongitude"]) + driftCoefficient * float(rel_sat["deltaDateRelative"] / 0.125) * 0.001
                if ascNodeLongitudeDeg < 0:
                    ascNodeLongitudeDeg = 360 + ascNodeLongitudeDeg
                elif ascNodeLongitudeDeg >= 360:
                    ascNodeLongitudeDeg = ascNodeLongitudeDeg - 360
                sat_data["ascNodeLongitudeDeg"] = ascNodeLongitudeDeg

                satellite_data_map[rel_address] = build_csv_row(rel_address[0], rel_date, sat_data, rel_name)

        elif "satellitesStatus" in entry:
            for status in entry["satellitesStatus"]:
                addr = status["satelliteAddress"]
                if addr in satellite_data_map:
                    down_status = downlink_status.get(status["payloadType"]) if status["payloadDownlinkMissionStatus"] else downlink_status.get("OFF")
                    up_status = uplink_status.get(status["payloadType"]) if status["payloadUplinkMissionStatus"] else uplink_status.get("OFF")
                    satellite_data_map[addr]["downlinkStatus"] = down_status
                    satellite_data_map[addr]["uplinkStatus"] = up_status

    # === FILTER on specific sat_list ===
    ## will must be done in the embedded side ?
    rows = list(satellite_data_map.values())

    if len(satellite_whitelist) > 0:
        rows = [row for row in rows if row["satName"].strip() in satellite_whitelist]

    output = StringIO("")
    if csv_file_path:
        # Write to CSV
        with open(csv_file_path, mode="w", newline=" ") as file:
            output = StringIO(" ".join([f"{row[field]}" for row in rows for field in fieldnames]))

            file.write(output.getvalue())

        output.seek(0)
        return output
    else:
        output = StringIO(" ".join([f"{row[field]}" for row in rows for field in fieldnames]))

        output.seek(0)

        # Add a space at the beginning to match the expected output format
        full_output = StringIO("")
        if len(rows) > 0:
            full_output.write(" ")
        full_output.write(output.getvalue())

        # === Build metadata from CSV rows ===
        metadata = build_metadata_from_csv_rows(rows)
        return full_output, metadata


# Example usage
if __name__ == "__main__":
    import sys

    # Example usage with the API
    api_url = sys.argv[1]
    headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN", "X-Kineis-Api-Key": "YOUR_API_KEY"}

    try:
        binary_data = fetch_binary_data(api_url, headers)
        parsed_data = parse_binary_data(binary_data)
        csv_file_path = "output1.csv"
        convert_to_csv(parsed_data, csv_file_path)
        logger.info(f"CSV data has been written to {csv_file_path}")
    except Exception as e:
        logger.error(f"Error: {e}")

    # Example usage with a file
    file_path = "path/to/your/binary/file.bin"

    try:
        binary_data = read_binary_data_from_file(file_path)
        parsed_data = parse_binary_data(binary_data)
        csv_file_path = "output2.csv"
        convert_to_csv(parsed_data, csv_file_path)
        logger.info(f"CSV data has been written to {csv_file_path}")
    except Exception as e:
        logger.error(f"Error: {e}")
