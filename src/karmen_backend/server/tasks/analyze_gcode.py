import re
from collections import defaultdict

from server import app, celery
from server.database import gcodes


# big kudos to https://github.com/eyal0/OctoPrint-PrintTimeGenius/blob/master/octoprint_PrintTimeGenius/analyzers/analyze_gcode_comments.py
# Large parts of the source are unchanged and are copyrighted to https://github.com/eyal0
# This one supports PrusaSlicer and Cura for now

TIME_UNITS_TO_SECONDS = defaultdict(
    lambda: 0,
    {
        "s": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,
        "min": 60,
        "minute": 60,
        "minutes": 60,
        "h": 60 * 60,
        "hour": 60 * 60,
        "hours": 60 * 60,
        "d": 24 * 60 * 60,
        "day": 24 * 60 * 60,
        "days": 24 * 60 * 60,
    },
)


def format_time_text(time_text):
    """Given a string like "5 minutes, 4 seconds + 82 hours" return the total in seconds"""
    total = 0
    for time_part in re.finditer(r"([0-9.]+)\s*([a-zA-Z]+)", time_text):
        quantity = float(time_part.group(1))
        units = TIME_UNITS_TO_SECONDS[time_part.group(2)]
        total += quantity * units
    return int(total)


def get_filament_used_length(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*filament used\s* \[mm\]\s*=\s*([0-9.]+)\s*", gcode_line)
        return float(m.group(1)) if m else None

    def cura(gcode_line):
        m = re.match(r"\s*;\s*Filament used\s*:\s*([0-9.]+)\s*m\s*", gcode_line)
        return float(m.group(1)) * 1000 if m else None

    def slic3r(gcode_line):
        m = re.match(
            r"\s*;\s*filament used\s*=\s*([0-9.]+)\s*mm\s*\(([0-9.]+)cm3\)\s*",
            gcode_line,
        )
        return float(m.group(1)) if m else None

    def simplify3d(gcode_line):
        m = re.match(
            r"\s*;\s*Filament length\s*:\s*([0-9.]+)\s*mm\s*\(([0-9.]+)\s*m\)\s*",
            gcode_line,
        )
        return float(m.group(1)) if m else None

    for fn in [prusaslicer, cura, slic3r, simplify3d]:
        result = fn(line)
        if result:
            return result
    return None


def get_filament_used_volume(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*filament used\s* \[cm3\]\s*=\s*([0-9.]+)\s*", gcode_line)
        return float(m.group(1)) if m else None

    def slic3r(gcode_line):
        m = re.match(
            r"\s*;\s*filament used\s*=\s*([0-9.]+)\s*mm\s*\(([0-9.]+)cm3\)\s*",
            gcode_line,
        )
        return float(m.group(2)) if m else None

    def simplify3d(gcode_line):
        m = re.match(
            r"\s*;\s*Plastic volume\s*:\s*([0-9.]+)\s*mm\^3\s*\(([0-9.]+)\s*cc\)\s*",
            gcode_line,
        )
        return float(m.group(2)) if m else None

    for fn in [prusaslicer, slic3r, simplify3d]:
        result = fn(line)
        if result:
            return result
    return None


def get_filament_type(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*filament_type\s*=\s*(\w+)\s*", gcode_line)
        return m.group(1).strip() if m else None

    def simplify3d(gcode_line):
        m = re.match(r"\s*;\s*printMaterial\s*,\s*(\w+)\s*", gcode_line)
        return m.group(1).strip() if m else None

    for fn in [prusaslicer, simplify3d]:
        result = fn(line)
        if result:
            return result
    return None


def get_temperature_bed(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*bed_temperature\s*=\s*(\w*)\s*", gcode_line)
        return float(m.group(1)) if m else None

    for fn in [prusaslicer]:
        result = fn(line)
        if result:
            return result
    return None


def get_temperature_bed_first(line):
    def prusaslicer(gcode_line):
        m = re.match(
            r"\s*;\s*first_layer_bed_temperature\s*=\s*([0-9.]+)\s*", gcode_line
        )
        return float(m.group(1)) if m else None

    for fn in [prusaslicer]:
        result = fn(line)
        if result:
            return result
    return None


def get_temperature_tool(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*temperature\s*=\s*([0-9.]+)\s*", gcode_line)
        return float(m.group(1)) if m else None

    for fn in [prusaslicer]:
        result = fn(line)
        if result:
            return result
    return None


def get_temperature_tool_first(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*first_layer_temperature\s*=\s*([0-9.]+)\s*", gcode_line)
        return float(m.group(1)) if m else None

    for fn in [prusaslicer]:
        result = fn(line)
        if result:
            return result
    return None


def get_time_estimate(line):
    def prusaslicer(gcode_line):
        m = re.match(
            r"\s*;\s*estimated printing time(?:.*normal.*)?\s*=\s*(.*)\s*", gcode_line
        )
        return format_time_text(m.group(1)) if m else None

    def cura(gcode_line):
        m = re.match(r"\s*;\s*TIME_ELAPSED\s*:\s*([0-9.]+)\s*", gcode_line)
        return int(float(m.group(1))) if m else None

    def simplify3d(gcode_line):
        m = re.match(r"\s*;\s*Build time\s*:\s*(.*)\s*", gcode_line)
        return format_time_text(m.group(1)) if m else None

    for fn in [prusaslicer, cura, simplify3d]:
        result = fn(line)
        if result:
            return result
    return None


def get_slicer(line):
    def prusaslicer(gcode_line):
        m = re.match(r"\s*;\s*generated by (.*) on.*", gcode_line, flags=re.IGNORECASE)
        return m.group(1) if m else None

    def cura(gcode_line):
        m = re.match(r"\s*;\s*generated with (.*)", gcode_line, flags=re.IGNORECASE)
        return m.group(1) if m else None

    def simplify3d(gcode_line):
        m = re.match(r"\s*;\s*G-Code generated by\s*(.*)\s*", gcode_line)
        return m.group(1) if m else None

    for fn in [prusaslicer, cura, simplify3d]:
        result = fn(line)
        if result:
            return result
    return None


@celery.task(name="analyze_gcode")
def analyze_gcode(gcode_id):
    gcode = gcodes.get_gcode(gcode_id)
    if not gcode:
        app.logger.error("Gcode does not exist in database")
        return
    # TODO if analysis already done on this file, skip
    try:
        result = {"filament": {}, "temperatures": {}, "time": {}, "slicer": None}
        # TODO this should be faster if we grep for only lines with ; in shell
        with open(gcode["absolute_path"]) as fp:
            for lno, rawline in enumerate(fp):
                stripped_line = rawline.rstrip()
                line = (
                    stripped_line.decode("utf-8")
                    if hasattr(stripped_line, "decode")
                    else stripped_line
                )
                if not line or line[0] not in ";M":
                    continue
                # TODO this supports only a single filament
                if not result["slicer"]:
                    result["slicer"] = get_slicer(line)
                filament_props = [
                    ("length_mm", get_filament_used_length),
                    ("volume_cm3", get_filament_used_volume),
                    ("type", get_filament_type),
                ]
                for fprop, evaluator in filament_props:
                    if not result["filament"].get(fprop, None):
                        result["filament"][fprop] = evaluator(line)
                # TODO this supports only a single tool
                temperature_props = [
                    ("bed", get_temperature_bed),
                    ("bed_first", get_temperature_bed_first),
                    ("tool0", get_temperature_tool),
                    ("tool0_first", get_temperature_tool_first),
                ]
                for fprop, evaluator in temperature_props:
                    if not result["temperatures"].get(fprop, None):
                        result["temperatures"][fprop] = evaluator(line)
                time_props = [("estimate_s", get_time_estimate)]
                for fprop, evaluator in time_props:
                    if not result["time"].get(fprop, None):
                        result["time"][fprop] = evaluator(line)
        gcodes.set_analysis(gcode_id, result)
    except FileNotFoundError:
        app.logger.error("Gcode file not found")
        return
