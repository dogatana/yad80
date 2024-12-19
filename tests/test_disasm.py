import subprocess
from pathlib import Path
import filecmp

ASM = r"C:\Programs\z88dk\bin\z80asm.exe"
BASE = Path(__file__).parent
TEMP_SRC = "temp.asm"
TEMP_OUT = "temp.bin"


def unlink_temp():
    for path in Path(".").glob("temp.*"):
        path.unlink(True)


def test_rom():
    for file in BASE.glob("*.rom"):
        unlink_temp()
        target = BASE / file

        result = subprocess.run(
            f"python -m yad80 -e -c 0-79 -- {target}".split(),
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, f"disasm {target}"

        Path(TEMP_SRC).write_text(result.stdout)
        result = subprocess.run([ASM, "-b", TEMP_SRC], stdout=True)
        assert result.returncode == 0, f"asm {TEMP_SRC} of {file}"

        assert filecmp.cmp(target, TEMP_OUT), f"compare {target} with {TEMP_OUT}"
    unlink_temp()


def test_MZT():
    for file in BASE.glob("*.mzt"):
        unlink_temp()
        target = BASE / file

        result = subprocess.run(
            f"python -m yad80 -e {target}".split(), text=True, capture_output=True
        )
        assert result.returncode == 0, f"diasm {target}"

        Path(TEMP_SRC).write_text(result.stdout)
        result = subprocess.run([ASM, "-b", TEMP_SRC], stdout=True)
        assert result.returncode == 0, f"asm {TEMP_SRC} of {file}"

        assert (
            target.read_bytes()[128:] == Path(TEMP_OUT).read_bytes()
        ), f"compare {target} with {TEMP_OUT}"
    unlink_temp()


def test_asm():
    for file in BASE.glob("*.bin"):
        unlink_temp()

        target = BASE / file
        result = subprocess.run(
            f"python -m yad80 -m 65536 {target}".split(), text=True, capture_output=True
        )
        assert result.returncode == 0, f"disasm {target}"

        Path(TEMP_SRC).write_text(result.stdout)
        result = subprocess.run([ASM, "-b", TEMP_SRC], stdout=True)
        assert result.returncode == 0, f"asm {TEMP_SRC} of {file}"

        assert (
            target.read_bytes() == Path(TEMP_OUT).read_bytes()
        ), f"compare {target} with {TEMP_OUT}"
    unlink_temp()
