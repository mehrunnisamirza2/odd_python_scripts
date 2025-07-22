import os
import sys
import math
import csv
from pathlib import Path
from typing import Optional
import acts
import acts.examples
from acts.examples import (
    ObjTrackingGeometryWriter,
    WhiteBoard,
    AlgorithmContext)


def getOpenDataDetectorDirectory():
    odd_dir = os.environ.get("ODD_PATH")
    if odd_dir is None:
        raise RuntimeError("ODD_PATH environment variable not set")
    odd_dir = Path(odd_dir)
    return odd_dir


def getOpenDataDetector(
    mdecorator=None,
    odd_dir: Optional[Path] = None,
    logLevel=acts.logging.VERBOSE,
):
    """This function sets up the open data detector. Requires DD4hep.
    Parameters
    ----------
    mdecorator: Material Decorator, take RootMaterialDecorator if non is given
    odd_dir: if not given, try to get via ODD_PATH environment variable
    logLevel: logging level
    """
    import acts.examples.dd4hep

    customLogLevel = acts.examples.defaultLogging(logLevel=logLevel)

    if odd_dir is None:
        odd_dir = getOpenDataDetectorDirectory()
    if not odd_dir.exists():
        raise RuntimeError(f"OpenDataDetector not found at {odd_dir}")

    odd_xml = odd_dir / "xml" / "OpenDataDetector.xml"
    if not odd_xml.exists():
        raise RuntimeError(f"OpenDataDetector.xml not found at {odd_xml}")

    env_vars = []
    map_name = "libOpenDataDetector.components"
    lib_name = None
    if sys.platform == "linux":
        env_vars = ["LD_LIBRARY_PATH"]
        lib_name = "libOpenDataDetector.so"
    elif sys.platform == "darwin":
        env_vars = ["DYLD_LIBRARY_PATH", "DD4HEP_LIBRARY_PATH"]
        lib_name = "libOpenDataDetector.dylib"

    if lib_name is not None and len(env_vars) > 0:
        found = False
        for env_var in env_vars:
            for lib_dir in os.environ.get(env_var, "").split(":"):
                lib_dir = Path(lib_dir)
                if (lib_dir / map_name).exists() and (lib_dir / lib_name).exists():
                    found = True
                    break
        if not found:
            msg = (
                "Unable to find OpenDataDetector factory library. "
                f"You might need to point {'/'.join(env_vars)} to build/thirdparty/OpenDataDetector/factory or other ODD install location"
            )
            raise RuntimeError(msg)

    volumeRadiusCutsMap = {
        28: [850.0],  # LStrip negative z -- only 2 rings
        30: [850.0],  # LStrip positive z
        23: [400.0, 550.0],  # SStrip negative z  -- only 3 rings
        25: [400.0, 550.0],  # SStrip positive z
        16: [100.0],  # Pixels negative z    -- only 2 rings
        18: [100.0],  # Pixels positive z
    }

    #clear file before starting to append 
    with open("odd_geoid_data.csv", mode='w', newline="") as file:
        writer = csv.writer(file)
        writer.writerow(['geoid', 'r']) #header
        # writer.writerow(['geoid']) #header

    def geoid_hook(geoid, surface):
        gctx = acts.GeometryContext()

        r = None # ensure r is defined even if volume not in the map

        if geoid.volume() in volumeRadiusCutsMap:
            r = math.sqrt(surface.center(gctx)[0] ** 2 + surface.center(gctx)[1] ** 2)
            print("r = ", r)

            geoid.setExtra(1)
            for cut in volumeRadiusCutsMap[geoid.volume()]:
                if r > cut:
                    geoid.setExtra(geoid.extra() + 1)

        print(geoid)  #check

        with open("odd_geoid_data.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([geoid, "r=",r])
            # writer.writerow([geoid])
    
        return geoid

    if mdecorator is None:
        mdecorator = acts.examples.RootMaterialDecorator(
            fileName=str(odd_dir / "data/odd-material-maps.root"),
            level=customLogLevel(minLevel=acts.logging.VERBOSE),
        )

    dd4hepConfig = acts.examples.dd4hep.DD4hepDetector.Config(
        xmlFileNames=[str(odd_xml)],
        name="OpenDataDetector",
        logLevel=acts.logging.VERBOSE,
        dd4hepLogLevel=acts.logging.VERBOSE,
        geometryIdentifierHook=acts.GeometryIdentifierHook(geoid_hook),
        materialDecorator=mdecorator,
    )
    detector = acts.examples.dd4hep.DD4hepDetector(dd4hepConfig)
    return detector

if __name__ == "__main__":
    ODD_detector = getOpenDataDetector()
    trackingGeometry = ODD_detector.trackingGeometry()
 
    print('got detector!!!')
 
    outputDir = ""
    os.makedirs(os.path.join(outputDir, "ODD_obj"), exist_ok=True)
 
    ialg = 0
    ievt = 0
    eventStore = WhiteBoard(name=f"EventStore#{ievt}", level=acts.logging.VERBOSE)
    context = AlgorithmContext(ialg, ievt, eventStore)
 
    writer = ObjTrackingGeometryWriter(level=acts.logging.VERBOSE, outputDir=os.path.join(outputDir, "ODD_obj"))
    print(f"Writing tracking geometry to {os.path.join(outputDir, 'ODD_obj')}")
    writer.write(context, trackingGeometry)