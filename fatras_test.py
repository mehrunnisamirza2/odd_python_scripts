#!/usr/bin/env python3
from pathlib import Path
import math

import acts
import acts.examples
from acts.examples.simulation import (
    addFatras,
    addParticleGun,
    EtaConfig,
    ParticleConfig,
    MomentumConfig,
    PhiConfig
)
# from acts.examples.odd import getOpenDataDetector

from odd_2 import getOpenDataDetector, getOpenDataDetectorDirectory
u = acts.UnitConstants


def runFatras(trackingGeometry, field, outputDir, s: acts.examples.Sequencer = None):
    s = s or acts.examples.Sequencer(events=1, numThreads=-1)
    s.config.logLevel = acts.logging.VERBOSE
    rnd = acts.examples.RandomNumbers(seed=42)

    addParticleGun(
        s,
        ParticleConfig(num=1, pdg=acts.PdgParticle.eMuon, randomizeCharge=True),
        EtaConfig(0, 0),
        MomentumConfig(1 * u.GeV, 1 * u.GeV, transverse=True),
        PhiConfig(1/2 * math.pi, 1/2 * math.pi),
        rnd=rnd,
    )
    outputDir = Path(outputDir)
    addFatras(
        s,
        trackingGeometry,
        field,
        outputDirCsv=outputDir / "csv",
        outputDirRoot=outputDir,
        outputDirObj=outputDir / 'obj',
        rnd=rnd,
        logLevel=acts.logging.VERBOSE,
    )
    return s


if "__main__" == __name__:
    # gdc = acts.examples.GenericDetector.Config()
    # gd = acts.examples.GenericDetector(gdc)
    # trackingGeometry, decorators, _ = gd.trackingGeometry()

    detector = getOpenDataDetector()
    # detector = acts.examples.GenericDetector()
    trackingGeometry = detector.trackingGeometry()

    field = acts.ConstantBField(acts.Vector3(0, 0, 2 * u.T))

    import os
    # os.makedirs(os.getcwd() + "/seeding_output", exist_ok=True)

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
    OUTPUT_DIR = os.path.join(BASE_DIR, "output", "fatras_output_test")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    runFatras(trackingGeometry, field, outputDir=OUTPUT_DIR).run()
