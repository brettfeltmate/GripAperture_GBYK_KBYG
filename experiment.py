# -*- coding: utf-8 -*-
#
# Paradigm exploring premptive grip aperture scaling under target uncertainty.
# Two objects presented within a given trial, the size of each (individually) is either 4 or 8cm
# Participants perform two task types (blocked):
# 	GBYK: Prior to response initiation, objects are equiprobably the target-to-be. 
#		  Velocity threshold used to trigger target reveal.
#	KBYG: Target is distinguised prior to response initiation.
# In both tasks, participants are to respond by reaching to pincer-grip the target object.

# As this design does not utilize eye-tracking, stimulus sizings are defined in cm. 
# The screen's physical dimensions are used to calculate the equivalent pixel size for stimuli at runtime.


__author__ = "Brett Feltmate"

import klibs
from klibs import P

from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLUserInterface import any_key, ui_request, key_pressed
from klibs.KLCommunication import message
from klibs.KLUtilities import hide_mouse_cursor, now
from klibs.KLAudio import Tone

from random import randrange, shuffle

import datatable as dt

from OptiTracker import OptiTracker

# timing constants
GO_SIGNAL_ONSET  = (500, 2000)
RESPONSE_TIMEOUT =  5000

# audio constants
TONE_DURATION = 50
TONE_SHAPE    = "sine"
TONE_FREQ     = 784      # ridin' on yo G5 airplane
TONE_VOLUME   = 0.5

# sizing constants
SMALL_CM  = 4
LARGE_CM  = 8
OFFSET_CM = 6
BRIM_CM   = 1

# fill constants
WHITE = (255, 255, 255, 255)
GRUE  = ( 90,  90,  96, 255)

# anti-typo protections
LEFT       = "left"
RIGHT      = "right"
SMALL 	   = "small"
LARGE 	   = "large"
TARGET     = "target"
DISTRACTOR = "distractor"
GBYK       = "GBYK"
KBYG       = "KBYG"

class GBYK_GripAperture(klibs.Experiment):

	def setup(self):
		# Define standard units
		PX_CM = round(P.ppi / 2.54)

		SMALL_PX = PX_CM * SMALL_CM
		LARGE_PX = PX_CM * LARGE_CM

		# Placeholder sizing properties
		OFFSET 	   = OFFSET_CM * PX_CM		
		BRIMWIDTH  = BRIM_CM * PX_CM   		
		SMALL_DIAM = SMALL_PX + BRIMWIDTH
		LARGE_DIAM = LARGE_PX + BRIMWIDTH

		# placeholder locs
		self.locs = {	# 12cm between placeholder centers
			LEFT:  (P.screen_c[0] - OFFSET, P.screen_c[1]),
			RIGHT: (P.screen_c[0] + OFFSET, P.screen_c[1])
		}


		# spawn default placeholders
		self.placeholders = {
			TARGET:{ 
				SMALL: kld.Annulus(SMALL_DIAM, BRIMWIDTH),
				LARGE: kld.Annulus(LARGE_DIAM, BRIMWIDTH)},
			DISTRACTOR: {
				SMALL: kld.Annulus(SMALL_DIAM, BRIMWIDTH),
				LARGE: kld.Annulus(LARGE_DIAM, BRIMWIDTH)}
		}

		self.go_signal = Tone(TONE_DURATION, TONE_SHAPE, TONE_FREQ, TONE_VOLUME)

		# TODO: Work out optitrack integration

		# randomize task sequence
		self.task_sequence = [GBYK, KBYG]
		shuffle(self.task_sequence)

		
		# Stitch in practice block per task if enabled
		if P.run_practice_blocks:
			self.task_sequence = [task for task in self.task_sequence for _ in range(2)]
			self.insert_practice_block(block_nums=[1, 3], trial_counts=P.trials_per_practice_block)


		# setup optitracker
		self.opti = OptiTracker()

		self.optidata = {
			"Prefix": 		     dt.Frame(),
			"MarkerSets": 	     dt.Frame(),
			"LegacyMarkerSet":   dt.Frame(),
			"LabeledMarkerSet":  dt.Frame(),
			"RigidBodies": 	     dt.Frame(),
			"Skeletons": 	     dt.Frame(),
			"AssetRigidBodies":  dt.Frame(),
			"AssetMarkers":      dt.Frame()
		}

		self.optidesc = {
			"MarkerSets": 	     dt.Frame(),
			"RigidBodies": 	     dt.Frame()
		}


	def block(self):
		# grab task
		self.block_task = self.task_sequence.pop(0)

		# instrux
		instrux = f"Task: {self.block_task}\n" + \
			  	  f"Block: {P.block_number} of {P.blocks_per_experiment}\n" + \
			   	   "(Instrux TBD, grab stuff)" + \
			       "\n\nAny key to start block."
		
		fill()
		message(instrux, location=P.screen_c)
		flip()

		any_key()

	def setup_response_collector(self):
		# TODO: Not sure if optitracker can be integrated with ResponseCollector...
		pass

	def trial_prep(self):
		# slight uncertainity in go signal
		self.evm.add_event("go_signal",        randrange(*GO_SIGNAL_ONSET))
		self.evm.add_event("response_timeout", RESPONSE_TIMEOUT, after = "go_signal")
		
		# TODO: integrate plato goggles
		
		# determine distractor position
		self.distractor_loc = LEFT if self.target_loc == RIGHT else RIGHT

		# setup phase
		self.present_stimuli(trial_prep = True)

		any_key()

		# base display
		self.present_stimuli()

		# start optitracker
		self.opti.start()


	def trial(self):
		hide_mouse_cursor()

		# TODO: open goggles

		# if KBYG, reveal target immediately
		if self.block_task == KBYG:
			self.present_stimuli(show_target = True)

		else:
			self.present_stimuli(gbyk_dev = True)


		while self.evm.before("go_signal"):
			ui_request()

		# signal to start
		self.go_signal.play()

		# monitor timings
		trial_start = now()
		timeout_at = trial_start + (RESPONSE_TIMEOUT // 1000)

		# TODO: remove in production
		if self.block_task == GBYK:
			show_target = False
			while not show_target:
				show_target = key_pressed()

		self.present_stimuli(show_target = True)




		# until response or timeout
		responded = False
		while now() < timeout_at and not responded:
			responded = key_pressed()

		self.opti.stop()

		return {
			"block_num":       P.block_number,
			"trial_num":       P.trial_number,
			"practicing":      P.practicing,
			"task_type":       self.block_task,
			"target_size": 	   self.target_size,
			"target_loc": 	   self.target_loc,
			"distractor_size": self.distractor_size,
			"distractor_loc":  self.distractor_loc,
			"response_time":   now() - trial_start,
			"movement_time":   "NA",
			"object_grasped":  "NA"
		}

	def trial_clean_up(self):
		trial_frames = self.opti.dataexport()

		for asset in trial_frames.keys():
			frame = trial_frames[asset]
			frame[:, 
			   dt.update(**{
					"participant_id"  : P.participant_id,
					"practicing"	  : P.practicing,
					"block_num"	      : P.block_number, 
					"trial_num"	      : P.trial_number, 
					"task_type"	      : self.block_task,
					"target_size"	  : self.target_size,
					"target_loc"      : self.target_loc, 
					"distractor_size" : self.distractor_size,
					"distractor_loc"  : self.distractor_loc
				}
			)]
			print("----------------------------------\n\n")
			print(f"data from B{P.block_number}-T{P.trial_number} clean up:\n")
			print(frame)
			print("----------------------------------\n\n")
			frame.to_csv(f"GripAperture_B{P.block_number}-T{P.trial_number}_{asset}_framedata.csv")

			self.optidata[asset] = dt.rbind(self.optidata[asset], frame)


		trial_frames = self.opti.descexport()

		for asset in trial_frames.keys():
			frame = trial_frames[asset]
			frame[:, 
			   dt.update(**{
					"participant_id"  : P.participant_id,
					"practicing"	  : P.practicing,
					"block_num"	      : P.block_number, 
					"trial_num"	      : P.trial_number, 
					"task_type"	      : self.block_task,
					"target_size"	  : self.target_size,
					"target_loc"      : self.target_loc, 
					"distractor_size" : self.distractor_size,
					"distractor_loc"  : self.distractor_loc
				}
			)]
			print("----------------------------------\n\n")
			print(f"desc from B{P.block_number}-T{P.trial_number} clean up:\n")
			print(frame)
			print("----------------------------------\n\n")
			frame.to_csv(f"GripAperture_B{P.block_number}-T{P.trial_number}_{asset}_framedesc.csv")

			self.optidesc[asset] = dt.rbind(self.optidesc[asset], frame)

	def clean_up(self):

		for asset in self.optidata.keys():
			print("----------------------------------\n\n")
			print("exp data final clean_up:\n")
			print(self.optidata[asset])
			print("----------------------------------\n\n")

			self.optidata[asset].to_csv(f"GripAperture_{asset}_framedata.csv", append=True)

		for asset in self.optidesc.keys():
			print("----------------------------------\n\n")
			print("exp desc final clean_up:\n")
			print(self.optidesc[asset])
			print("----------------------------------\n\n")

			self.optidesc[asset].to_csv(f"GripAperture_{asset}_framedesc.csv", append=True)

	def present_stimuli(self, trial_prep = False, show_target = False, gbyk_dev = False):
		fill()

		if trial_prep:
			message( 
		   		"Place props within size-matched rings.\n\nKeypress to start trial.",
		   		location=[P.screen_c[0], P.screen_c[1] // 3]
		   )
			
		if gbyk_dev:
			message(
				"GBYK Development Mode\n\nPress any key to reveal target.",
				location = [P.screen_c[0], P.screen_c[1] // 3]
			)

		distractor_holder      = self.placeholders[DISTRACTOR][self.distractor_size]
		distractor_holder.fill = GRUE

		target_holder	       = self.placeholders[TARGET][self.target_size]
		target_holder.fill     = WHITE if show_target else GRUE


		blit(distractor_holder, registration=5, location=self.locs[self.distractor_loc])
		blit(target_holder,     registration=5, location=self.locs[self.target_loc])


		flip()


