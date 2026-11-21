import runpy
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BUILDER = Path(__file__).resolve().parents[1] / "builder" / "fpga_builder.py"
namespace = runpy.run_path(str(BUILDER), init_globals={"Import": lambda _: None, "env": {}})
scan_libraries = namespace["scan_library_sources"]
scan_project = namespace["scan_fpga_sources"]
update_project = namespace["update_gprj_file"]
build_fpga = namespace["build_fpga_action"]


class FakeEnv:
    def __init__(self, root, deps, exclusions=""):
        self.root = root
        self.deps = deps
        self.exclusions = exclusions

    def GetProjectOption(self, name, default):
        return self.deps if name == "lib_deps" else default

    def subst(self, value):
        return str(self.root) if value == "$PROJECT_LIBDEPS_DIR" else "fpga"

    def BoardConfig(self):
        return {"build.fpga_exclude_sources": self.exclusions}


class LibraryGatewareTests(unittest.TestCase):
    def test_dependency_closure_headers_exclusions_and_stale_libraries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packages = {}
            for name in ("main", "dependency", "stale"):
                package = root / "fpga" / name
                gateware = package / "gateware"
                gateware.mkdir(parents=True)
                (gateware / f"{name}.v").write_text("module placeholder; endmodule")
                packages[name] = SimpleNamespace(path=str(package))
            (root / "fpga" / "main" / "gateware" / "defs.vh").write_text("`define TEST")
            (root / "fpga" / "dependency" / "gateware" / "ignored.v").touch()
            (root / "fpga" / "main" / "gateware" / "board.cst").touch()

            manager = SimpleNamespace(
                get_package=lambda spec: packages.get(spec),
                get_pkg_dependencies=lambda pkg: (
                    [{"name": "dependency"}, {"name": "optional", "optional": True}]
                    if Path(pkg.path).name == "main" else []
                ),
                dependency_to_spec=lambda dep: dep["name"],
            )
            env = FakeEnv(root, ["main"], "dependency/gateware/ignored.v")
            with patch.dict(scan_libraries.__globals__, {"LibraryPackageManager": lambda _: manager}):
                result = scan_libraries(env)

            self.assertEqual({p.name for p in result["verilog"]}, {"main.v", "dependency.v"})
            self.assertEqual([p.name for p in result["headers"]], ["defs.vh"])
            self.assertEqual(result["vhdl"], [])

    def test_missing_required_dependency_fails(self):
        manager = SimpleNamespace(get_package=lambda spec: None)
        with patch.dict(scan_libraries.__globals__, {"LibraryPackageManager": lambda _: manager}):
            with self.assertRaisesRegex(RuntimeError, "not installed: missing"):
                scan_libraries(FakeEnv(Path("unused"), ["missing"]))

    def test_project_update_preserves_ip_and_removes_stale_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fpga = root / "fpga"
            source = fpga / "src"
            source.mkdir(parents=True)
            constraints = fpga / "constraints"
            constraints.mkdir()
            (source / "top.v").touch()
            (source / "defs.vh").touch()
            (constraints / "pins.cst").touch()
            libdeps = root / ".pio" / "libdeps" / "fpga"
            gateware = libdeps / "device" / "gateware"
            gateware.mkdir(parents=True)
            (gateware / "device.v").touch()
            project = fpga / "project.gprj"
            project.write_text(
                '<Project><FileList>'
                '<File path="ip/core.ipc" type="file.ipc" enable="1"/>'
                '<File path="src/other.ipc" type="file.ipc" enable="1"/>'
                '<File path="constraints/timing.sdc" type="file.sdc" enable="1"/>'
                '<File path="../.pio/libdeps/fpga/old/gateware/old.v" type="file.verilog" enable="1"/>'
                '</FileList></Project>'
            )
            project_sources = scan_project(fpga)
            libraries = {"verilog": [gateware / "device.v"], "vhdl": [], "headers": []}
            update_project(project, project_sources, fpga, libraries, libdeps)
            update_project(project, project_sources, fpga, libraries, libdeps)

            paths = [entry.get("path") for entry in ET.parse(project).findall("./FileList/File")]
            self.assertEqual(paths, [
                "ip/core.ipc", "src/other.ipc", "constraints/timing.sdc",
                "src/top.v", "constraints/pins.cst",
                "../.pio/libdeps/fpga/device/gateware/device.v",
            ])

    def test_build_passes_multiple_header_directories_to_gowin(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fpga = root / "fpga"
            source = fpga / "src"
            source.mkdir(parents=True)
            (source / "top.v").touch()
            (source / "project.vh").touch()
            library = root / ".pio" / "libdeps" / "fpga" / "device" / "gateware"
            library.mkdir(parents=True)
            (library / "device.vh").touch()
            (fpga / "project.gprj").write_text("<Project><FileList/></Project>")
            output = fpga / "impl" / "pnr"
            output.mkdir(parents=True)
            custom_include = (root / "custom_headers").as_posix()
            old_library = (root / ".pio" / "libdeps" / "fpga" / "old" / "gateware").as_posix()
            (fpga / "impl" / "project_process_config.json").write_text(json.dumps({
                "IncludePath": [custom_include, old_library],
            }))
            (output / "project.bin").write_bytes(b"bitstream")
            build_dir = root / "build"
            build_dir.mkdir()

            class BuildEnv(FakeEnv):
                def get(self, name):
                    return str(root) if name == "PROJECT_DIR" else None

                def subst(self, value):
                    if value == "$BUILD_DIR":
                        return str(build_dir)
                    if value == "$PROJECT_LIBDEPS_DIR":
                        return str(root / ".pio" / "libdeps")
                    return "fpga"

                def Depends(self, target, sources):
                    self.dependencies = sources

            env = BuildEnv(root, [])
            library_sources = {"verilog": [], "vhdl": [], "headers": [library / "device.vh"]}
            result = SimpleNamespace(stdout="", stderr="", returncode=0)
            with patch.dict(build_fpga.__globals__, {
                "find_gowin_toolchain": lambda _: root,
                "find_gw_sh": lambda _: root / "gw_sh",
                "scan_library_sources": lambda _: library_sources,
            }), patch.object(namespace["subprocess"], "run", return_value=result):
                self.assertEqual(build_fpga([], [], env), 0)

            script = (fpga / "impl" / "build_script.tcl").read_text()
            paths = ";".join([custom_include] + sorted([source.resolve().as_posix(), library.resolve().as_posix()]))
            self.assertIn(f"set_option -include_path {{{paths}}}", script)
            self.assertIn(str(library / "device.vh"), env.dependencies)
            self.assertNotIn(".vh", (fpga / "project.gprj").read_text())


if __name__ == "__main__":
    unittest.main()
