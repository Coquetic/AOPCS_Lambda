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

###########################################################################
## For Security reason, most of informations to decode trame are removed ##
###########################################################################

# Enum for payloadType
class PayloadType(Enum):

# Enum for formatReference
class FormatReference(Enum):

# Satellite identification table (Satellite Address (hexadecimal coding) : Satellite Mnemonic)
satellite_identification = {
    "XX": "XX",
}

downlink_status = {}

uplink_status = {}


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
        # broadcaster_reference = int(0)
        format_reference = 0
        # if elif .. MONOSAT or MULTISAT

    return parsed_data


# Function to parse AOP Multisat format
def parse_aop_multisat(bit_data: str, index: int) -> ParsedData:
    aop_multisat: ParsedData = {}
    # MULTISAT Treatment
    return aop_multisat


# Function to parse AOP Monosat format
def parse_aop_monosat(bit_data: str, index: int) -> ParsedData:
    aop_monosat: ParsedData = {}
    # MONOSAT Treatment
    return aop_monosat


# Function to parse Constellation Status format
def parse_constellation_status(bit_data: str, index: int, format_reference: int) -> ParsedData:
    constellation_status: ParsedData = {}
    #Constellation status Treatment
    return constellation_status


# Function to parse satellite data
def parse_aop_satellite_data(bit_data: str, index: int) -> ParsedData:
    satellite_data: ParsedData = {}
    # Satellite data Treatment
    return satellite_data


# Function to parse relative satellite data
def parse_aop_relative_satellite(bit_data: str, index: int) -> ParsedData:
    relative_satellite: ParsedData = {}
    # Relative Satellite Treatment
    return relative_satellite


# Function to parse satellite status
def parse_satellite_status(bit_data: str, index: int) -> ParsedData:
    satellite_status: ParsedData = {}
    # Satellite Status Treatment
    return satellite_status


# Function to get the format size in bits
def get_format_size_in_bits(format_reference: int) -> int:
    if format_reference == FormatReference.AOP_MULTISAT.value:
        return 0
    elif format_reference == FormatReference.AOP_MONOSAT.value:
        return 1
    elif format_reference == FormatReference.CS_2_SAT.value:
        return 2
    elif format_reference == FormatReference.CS_10_SAT.value:
        return 3
    elif format_reference == FormatReference.CS_17_SAT.value:
        return 4
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
