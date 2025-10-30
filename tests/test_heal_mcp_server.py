import importlib
import sys
import types


def test_create_mcp_with_fake_fastmcp():
    """Ensure create_mcp() returns an object produced by FastMCP.from_openapi.

    The real `fastmcp` package may not be available in test environments, so
    inject a fake `fastmcp` module with a minimal `FastMCP` implementation.
    """

    # Create a fake fastmcp module (manual injection so tests can run
    # without pytest fixtures present)
    fake_fastmcp = types.ModuleType("fastmcp")

    class FakeFastMCP:
        def __init__(self, name=None):
            self.name = name

        @classmethod
        def from_openapi(cls, url, name=None):
            # Verify the URL shape is passed through in real code; keep simple here
            assert isinstance(url, str) and url.startswith("http")
            return cls(name=name)

        def run(self, *args, **kwargs):
            # no-op for tests
            return None

    fake_fastmcp.FastMCP = FakeFastMCP

    # Inject into sys.modules so imports inside the module under test will use it
    orig = sys.modules.get("fastmcp")
    sys.modules["fastmcp"] = fake_fastmcp
    try:
        # Ensure the module under test is re-imported fresh
        if "src.heal_mcp_server" in sys.modules:
            del sys.modules["src.heal_mcp_server"]

        m = importlib.import_module("src.heal_mcp_server")
        importlib.reload(m)

        mcp = m.create_mcp()
    finally:
        # restore original fastmcp if present
        if orig is None:
            del sys.modules["fastmcp"]
        else:
            sys.modules["fastmcp"] = orig
    assert hasattr(mcp, "run")
    assert getattr(mcp, "name", None) == "heal-search-mcp"
