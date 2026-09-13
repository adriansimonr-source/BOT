import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packaging/windows/AppxManifest.xml.in"
NS = {
    "foundation": (
        "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
    ),
    "uap10": "http://schemas.microsoft.com/appx/manifest/uap/windows10/10",
    "uap11": "http://schemas.microsoft.com/appx/manifest/uap/windows10/11",
    "rescap": (
        "http://schemas.microsoft.com/appx/manifest/"
        "foundation/windows10/restrictedcapabilities"
    ),
}


class MsixManifestTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(MANIFEST).getroot()

    def test_targets_every_windows_11_desktop_build(self):
        family = self.root.find(
            "foundation:Dependencies/foundation:TargetDeviceFamily",
            NS,
        )

        self.assertIsNotNone(family)
        self.assertEqual(family.get("Name"), "Windows.Desktop")
        self.assertEqual(family.get("MinVersion"), "10.0.22000.0")

    def test_declares_full_trust_and_capture_capabilities(self):
        capabilities = {
            element.get("Name")
            for element in self.root.findall("foundation:Capabilities/*", NS)
        }
        application = self.root.find(
            "foundation:Applications/foundation:Application",
            NS,
        )

        self.assertEqual(
            capabilities,
            {
                "graphicsCaptureProgrammatic",
                "graphicsCaptureWithoutBorder",
                "runFullTrust",
            },
        )
        self.assertEqual(
            application.get(f"{{{NS['uap10']}}}RuntimeBehavior"),
            "packagedClassicApp",
        )
        self.assertEqual(
            application.get(f"{{{NS['uap10']}}}TrustLevel"),
            "mediumIL",
        )


if __name__ == "__main__":
    unittest.main()
