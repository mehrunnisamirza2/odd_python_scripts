#!/usr/bin/env python3
import math
import os
import acts
import acts.examples
from acts.examples import GenericDetector, AlignedDetector
from acts.examples.odd import getOpenDataDetectorDirectory
from acts.examples.simulation import (
    addParticleGun,
    EtaConfig,
    ParticleConfig,
    MomentumConfig,
    addSimWriters,
    PhiConfig
)
from pathlib import Path

u = acts.UnitConstants

# import sys
# from pathlib import Path

# # Add the directory containing fcchh_2.py to sys.path
# fcchh_script_path = Path("/Users/mehrunnisamirza/project/FCCDetectors/Detector/DetFCChhBaseline1/compact")
# sys.path.append(str(fcchh_script_path))

# Now import the function

from odd_2 import getOpenDataDetector, getOpenDataDetectorDirectory

def runPropagation(trackingGeometry, field, outputDir, s=None):

    s = s or acts.examples.Sequencer(events=1, numThreads=1, logLevel=acts.logging.VERBOSE)

    # for d in decorators:
    #     s.addContextDecorator(d)
    
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

    trkParamExtractor = acts.examples.ParticleTrackParamExtractor(
        level=acts.logging.VERBOSE,
        inputParticles="particles_input",
        outputTrackParameters="params_particles_input",
    )
    s.addAlgorithm(trkParamExtractor)

    nav_cfg = acts.Navigator.Config()
    nav_cfg.trackingGeometry = trackingGeometry 
    nav_cfg.resolveMaterial = False

    nav = acts.Navigator(nav_cfg, level=acts.logging.VERBOSE)

    # stepper = acts.EigenStepper(field)
    stepper = acts.SympyStepper(field)
    # stepper = acts.AtlasStepper(field)
    # stepper = acts.StraightLineStepper()

    propagator = acts.examples.ConcretePropagator(acts.Propagator(stepper, nav,loglevel=acts.logging.VERBOSE))

    propagationAlgorithm = acts.examples.PropagationAlgorithm(
        propagatorImpl=propagator,
        level=acts.logging.VERBOSE,
        sterileLogger=False,
        inputTrackParameters="params_particles_input",
        outputSummaryCollection="propagation_summary",
        debugOutput = True,
    )
    s.addAlgorithm(propagationAlgorithm)

    s.addWriter(
        acts.examples.RootPropagationSummaryWriter(
            level=acts.logging.VERBOSE,
            inputSummaryCollection="propagation_summary",
            filePath=outputDir + "/propagation_summary.root",
        )
    )

    # Common: Write the steps
    s.addWriter(
        acts.examples.RootPropagationStepsWriter(
            level=acts.logging.VERBOSE,
            collection="propagation_summary",
            filePath=outputDir + "/propagation_steps.root",
            )
        )
    
    #  # Common: read sim hits
    # s.addReader(
    #     acts.examples.RootSimHitReader(
    #         level=acts.logging.VERBOSE,
    #         outputSimHits="simhits",
    #         treeName="propagation_steps",
    #         filePath=outputDir + "/propagation_steps.root",
    #         )
    #     )
    return s


if "__main__" == __name__:
    matDeco = None
    # matDeco = acts.IMaterialDecorator.fromFile("material.json")
    # matDeco = acts.IMaterialDecorator.fromFile("material.root")

    ## Generic detector: Default
    detector = getOpenDataDetector()

    ## Alternative: Aligned detector in a couple of modes
    # detector = AlignedDetector(
    #     decoratorLogLevel=acts.logging.INFO,
    #     # These parameters need to be tuned so that GC doesn't break
    #     # with multiple threads
    #     iovSize=10,
    #     flushSize=10,
    #     # External alignment store
    #     mode=AlignedDetector.Config.Mode.External,
    #     # OR: Internal alignment storage
    #     # mode=AlignedDetector.Config.Mode.Internal,
    # )

    ## Alternative: DD4hep detector
    # dd4hepCfg = acts.examples.DD4hepDetector.Config()
    # dd4hepCfg.xmlFileNames = [str(getOpenDataDetectorDirectory()/"xml/OpenDataDetector.xml")]
    # detector = acts.examples.DD4hepDetector(dd4hepCfg)

    trackingGeometry = detector.trackingGeometry()
    # contextDecorators = detector.contextDecorators() #included this rather than none..otherwise doesnt work


    ## Magnetic field setup: Default: constant 2T longitudinal field
    field = acts.ConstantBField(acts.Vector3(0, 0, 2 * acts.UnitConstants.T)) 

    ## Alternative: no B field
    # field = acts.NullBField()

    ## Alternative: Analytical solenoid B field, discretized in an interpolated field map
    # solenoid = acts.SolenoidBField(
    #     radius = 1200*u.mm,
    #     length = 6000*u.mm,
    #     bMagCenter = 2*u.T,
    #     nCoils = 1194
    # )
    # field = acts.solenoidFieldMap(
    #     rlim=(0, 1200*u.mm),
    #     zlim=(-5000*u.mm, 5000*u.mm),
    #     nbins=(50, 50),
    #     field=solenoid
    # )

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
    OUTPUT_DIR = os.path.join(BASE_DIR, "output", "propagation_test_output")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    runPropagation(
        trackingGeometry,
        field,
        OUTPUT_DIR,
        # decorators=contextDecorators,
    ).run()
