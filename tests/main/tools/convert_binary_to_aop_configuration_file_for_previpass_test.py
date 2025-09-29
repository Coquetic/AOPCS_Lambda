import datetime
import json
from pathlib import Path
import re
from typing import Any, List
import pytest
from pytest import MonkeyPatch
from io import StringIO

import aopcs_lambda.src.tools.convert_binary_to_aop_configuration_file_for_previpass as module
from aopcs_lambda.src.tools.convert_binary_to_aop_configuration_file_for_previpass import convert_to_csv, parse_binary_data


class TestParseBinaryData:
    """Test of parse_binary_data function"""

    @pytest.fixture
    def binary_data(self) -> bytes:
        # I removed the file for the public repo
        binary_path = Path(__file__).parent / "test_data" / "binary_data.bin"
        with open(binary_path, "rb") as f:
            return f.read()

    @pytest.fixture
    def expected_data(self) -> Any:
        expected_parsed_data_path = Path(__file__).parent / "test_data" / "expected_parsed_data.json"
        with open(expected_parsed_data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_parse_binary_data_matches_expected(self, binary_data: bytes, expected_data: Any) -> None:
        result = parse_binary_data(binary_data)
        assert result == expected_data

    def test_parse_invalid_binary_data(self) -> None:
        invalid_data = b"\x01\x00\x00"
        with pytest.raises(Exception, match="Unknown format reference"):
            parse_binary_data(invalid_data)

    def test_parse_large_input_performance(self, binary_data: bytes) -> None:
        large_data = binary_data * 100
        result = parse_binary_data(large_data)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(entry, dict) for entry in result)

    def test_parse_binary_data_matches_metadatas(self, binary_data: bytes, expected_data: Any, set_env_vars: None) -> None:
        parsed_data = parse_binary_data(binary_data)

        # Generate the CSV
        csv_output, metadata = convert_to_csv(parsed_data)
        csv_text = csv_output.getvalue()

        # Retrieve dates in the CSV
        tuples = re.findall(r"\b(\d{4})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\b", csv_text)
        assert tuples, f"Aucune date trouvée dans le CSV: {csv_text!r}"

        csv_dates = [datetime.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), tzinfo=datetime.timezone.utc) for (y, mo, d, h, mi, s) in tuples]

        meta_min = metadata.satellite_prevision_min_date.replace(microsecond=0) if metadata.satellite_prevision_min_date else None
        meta_max = metadata.satellite_prevision_max_date.replace(microsecond=0) if metadata.satellite_prevision_max_date else None

        assert min(csv_dates) == meta_min
        assert max(csv_dates) == meta_max


class TestConvertToCsv:
    """Test of convert_to_csv function"""

    @staticmethod
    def parse_csv_output(output: StringIO) -> List[List[str]]:
        lines = output.getvalue().splitlines()
        a = [line.strip().split(" ") for line in lines]
        return a

    @pytest.fixture(autouse=True)
    def patch_satellite_identification(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setitem(
            module.convert_to_csv.__globals__,
            "satellite_identification",
            {"1234": "1234", "5678": "5678", "91011": "91011", "2222": "2222", "3333": "3333"},
        )
        monkeypatch.setitem(module.convert_to_csv.__globals__, "downlink_status", {"TYPE1": "DL-ON", "OFF": "DL-OFF"})
        monkeypatch.setitem(module.convert_to_csv.__globals__, "uplink_status", {"TYPE1": "UL-ON", "OFF": "UL-OFF"})

    def test_empty_input(self) -> None:
        csv_output, metadata = convert_to_csv([])
        rows = self.parse_csv_output(csv_output)
        assert rows == []
        assert metadata.satellite_prevision_min_date is None
        assert metadata.satellite_prevision_max_date is None

    def test_single_satellite(self) -> None:
        parsed_data = [
            {
                "satelliteReference": {
                    "satelliteAddress": "1234",
                    "date": "2025-05-15T12:00:00",
                    "semiMajorAxis": 6789000.0,
                    "inclination": 98.7,
                    "anLongitude": 123.4,
                    "anLongitudeDrift": 0.01,
                    "nodalPeriod": 96.5,
                    "semiMajorAxisDecay": 0.5,
                },
                "relativeSatellites": [
                    {
                        "satelliteAddressRelative": "91011",
                        "deltaDateRelative": 8,  # +1 sec
                    }
                ],
            }
        ]
        csv_output, metadata = convert_to_csv(parsed_data)
        rows = self.parse_csv_output(csv_output)
        assert (
            csv_output.getvalue()
            == " 1234 1 0   2025 05 15 12 00 00  6789.000  98.7000  123.400    0.010   96.5000   0.50"
            + " 91011 9 0   2025 05 15 12 00 08  6789.000  98.7000  123.400    0.010   96.5000   0.50"
        )
        sat_names = [row[0].strip() for row in rows]
        assert "1234" in sat_names[0], sat_names

        assert metadata.satellite_prevision_min_date is not None
        assert metadata.satellite_prevision_max_date is not None

    def test_satellite_with_relative(self) -> None:
        parsed_data = [
            {
                "satelliteData": {
                    "satelliteAddress": "5678",
                    "date": "2025-05-15T12:00:00",
                    "semiMajorAxis": 7000.0,
                    "inclination": 97.0,
                    "anLongitude": 130.0,
                    "anLongitudeDrift": 0.02,
                    "nodalPeriod": 95.0,
                    "semiMajorAxisDecay": 0.6,
                },
                "relativeSatellites": [
                    {
                        "satelliteAddressRelative": "91011",
                        "deltaDateRelative": 8,  # +1 sec
                    }
                ],
            }
        ]
        csv_output, metadata = convert_to_csv(parsed_data)
        rows = self.parse_csv_output(csv_output)

        assert any(cell.strip() == "5678" for row in rows for cell in row), rows
        assert any(cell.strip() == "91011" for row in rows for cell in row), rows[0]

        assert (
            csv_output.getvalue()
            == " 5678 5 0   2025 05 15 12 00 00     7.000  97.0000  130.000    0.020   95.0000   0.60 91011 9 0   2025 05 15 12 00 08     7.000  97.0000  130.000    0.020   95.0000   0.60"
        )

    def test_satellite_with_status(self) -> None:
        parsed_data: list[dict[str, Any]] = [
            {
                "satelliteReference": {
                    "satelliteAddress": "2222",
                    "date": "2025-05-15T12:00:00",
                    "semiMajorAxis": 7000.0,
                    "inclination": 97.5,
                    "anLongitude": 125.0,
                    "anLongitudeDrift": 0.015,
                    "nodalPeriod": 96.0,
                    "semiMajorAxisDecay": 0.55,
                }
            },
            {
                "satellitesStatus": [
                    {"satelliteAddress": "2222", "payloadType": "TYPE1", "payloadDownlinkMissionStatus": True, "payloadUplinkMissionStatus": False}
                ]
            },
        ]
        csv_output, metadata = convert_to_csv(parsed_data)
        rows = self.parse_csv_output(csv_output)
        assert any("DL-ON" in row and "UL-OFF" in row for row in rows)

    def test_multiple_satellites(self) -> None:
        parsed_data: list[dict[str, Any]] = [
            {
                "satelliteReference": {
                    "satelliteAddress": "1234",
                    "date": "2025-05-15T12:00:00",
                    "semiMajorAxis": 6789.0,
                    "inclination": 98.7,
                    "anLongitude": 123.4,
                    "anLongitudeDrift": 0.01,
                    "nodalPeriod": 96.5,
                    "semiMajorAxisDecay": 0.5,
                }
            },
            {
                "satelliteReference": {
                    "satelliteAddress": "3333",
                    "date": "2025-05-15T12:05:00",
                    "semiMajorAxis": 6790.0,
                    "inclination": 99.1,
                    "anLongitude": 124.0,
                    "anLongitudeDrift": 0.02,
                    "nodalPeriod": 97.0,
                    "semiMajorAxisDecay": 0.6,
                }
            },
            {
                "satellitesStatus": [
                    {"satelliteAddress": "1234", "payloadType": "TYPE1", "payloadDownlinkMissionStatus": False, "payloadUplinkMissionStatus": False},
                    {"satelliteAddress": "3333", "payloadType": "TYPE1", "payloadDownlinkMissionStatus": True, "payloadUplinkMissionStatus": True},
                ]
            },
        ]
        csv_output, metadata = convert_to_csv(parsed_data)
        rows = self.parse_csv_output(csv_output)
        for row in rows:
            if "1234" in row:
                assert "DL-OFF" in row and "UL-OFF" in row
            if "3333" in row:
                assert "DL-ON" in row and "UL-ON" in row
