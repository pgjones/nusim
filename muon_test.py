#!/usr/bin/env python
#
# muon_test
#
# Fires muons towards a cavity in rock, to see which muons make it through. For testing g4py.
#
# Author P G Jones - 2014-08-24 <p.g.jones@qmul.ac.uk> : New file.
####################################################################################################
import Geant4
import math

target_radius = 20.0 * Geant4.m
target_height = 20.0 * Geant4.m
detector = None # Global sensitive detector

class TargetDetector(Geant4.G4VSensitiveDetector):
    """ A sensitive detector."""
    def __init__(self):
        Geant4.G4VSensitiveDetector.__init__(self, "TargetDetector")
        self._total_deposit = 0.0
    def ProcessHits(self, step, history):
        """ Process a *step* in the detector.
        :param step: to process
        """
        self._total_deposit += step.GetTotalEnergyDeposit()
    def EndOfEvent(self, hit_collection):
        """ Print the total energy deposited in the detector."""
        print "Energy deposited in event =", self._total_deposit, "MeV"
        self._total_deposit = 0.0

class MuonTestGeometry(Geant4.G4VUserDetectorConstruction):
    """ This generates a box geometry, with a hole."""
    def Construct(self):
        """ Construct the geometry, return the world."""
        # First get the materials
        rock = Geant4.gNistManager.FindOrBuildMaterial("G4_SILICON_DIOXIDE") #Sandy rock
        air = Geant4.gNistManager.FindOrBuildMaterial("G4_AIR")
        # World is a 60x60x60m box
        world_solid = Geant4.G4Box("world_solid", 60.0 * Geant4.m, 60.0 * Geant4.m, 60.0 * Geant4.m)
        world_logical = Geant4.G4LogicalVolume(world_solid, rock, "world_logical")
        # Must be global in order not to be garbage collected
        global world
        world = Geant4.G4PVPlacement(Geant4.G4Transform3D(), world_logical, "world", None, False, 0)
        # The target volume is a 20x20m Cylinder in the centre
        target_solid = Geant4.G4Tubs("target_solid", 0.0, target_radius, target_height, 0.0, 2.0 * Geant4.pi)
        global detector
        detector = TargetDetector()
        target_logical = Geant4.G4LogicalVolume(target_solid, air, "target_logical", None, detector)
        # Must be global in order not to be garbage collected
        global target
        target = Geant4.G4PVPlacement(Geant4.G4Transform3D(), target_logical, "world", world_logical, False, 0)
        return world        

class MuonTestGenerator(Geant4.G4VUserPrimaryGeneratorAction):
    """ This generates muons on the x-y plane downwards.
    :param _particle_gun: A particle gun generator
    """
    
    def __init__(self):
        """ Set the default particle gun settings."""
        Geant4.G4VUserPrimaryGeneratorAction.__init__(self)
        self._particle_gun = Geant4.G4ParticleGun(1)
        self._particle_gun.SetParticleByName("mu-")
        self._particle_gun.SetParticleEnergy(230.0 * Geant4.GeV)
        self._particle_gun.SetParticleMomentumDirection(Geant4.G4ThreeVector(0.0, 0.0, -1.0))
    def GeneratePrimaries(self, event):
        """ This method is called by geant4 to fill the event with particles."""
        # As shooting down, generate positions on the x/y plane
        radius = math.sqrt(Geant4.G4UniformRand() * (30.0 * Geant4.m)**2)
        theta = Geant4.G4UniformRand() * 2.0 * Geant4.pi;
        position = Geant4.G4ThreeVector(math.cos(theta) * radius, math.sin(theta) * radius, 60.0 * Geant4.m)
        self._particle_gun.SetParticlePosition(position)
        return self._particle_gun.GeneratePrimaryVertex(event)

class EventAction(Geant4.G4UserEventAction):
    """ This clears the globals for each event."""
    def EndOfEventAction(self, event):
        """ Simply print out the deposited energy and reset it for the next event."""
        detector.EndOfEvent(None)

if __name__ == "__main__":
    # Note: The weird syntax whereby objects are assigned is required to keep them globally alive
    # Set the geometry construction
    geometry = MuonTestGeometry()
    Geant4.gRunManager.SetUserInitialization(geometry)
    # Now choose a physics list, FTFP_BERT sounds safe...
    physics = Geant4.FTFP_BERT()
    Geant4.gRunManager.SetUserInitialization(physics)
    # Now the generator
    generator = MuonTestGenerator()
    #generator.init()
    Geant4.gRunManager.SetUserAction(generator)
    # Add per event code
    event = EventAction()
    Geant4.gRunManager.SetUserAction(event)
                       
    # Can now initialise
    Geant4.gRunManager.Initialize()

    # Run N events
    Geant4.gRunManager.BeamOn(10)
