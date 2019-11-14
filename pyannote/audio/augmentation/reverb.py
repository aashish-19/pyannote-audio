#!/usr/bin/env python
# encoding: utf-8

# The MIT License (MIT)

# Copyright (c) 2019 CNRS

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# AUTHORS
# Hervé BREDIN - http://herve.niderb.fr

from typing import Tuple
from .base import Augmentation
import pyroomacoustics as pra
import numpy as np


normalize = lambda wav: wav / (np.sqrt(np.mean(wav ** 2)) + 1e-8)


class Reverb(Augmentation):
    """Simulate indoor reverberation

    Parameters
    ----------
    depth : (float, float), optional
        Minimum and maximum values for room depth (in meters).
        Defaults to (2.0, 10.0).
    width : (float, float), optional
        Minimum and maximum values for room width (in meters).
        Defaults to (1.0, 10.0).
    heigth : (float, float), optional
        Minimum and maximum values for room heigth (in meters).
        Defaults to (2.0, 5.0).
    absorption : (float, float), optional
        Minimum and maximum values of walls absorption coefficient.
        Defaults to (0.2, 0.9).
    """


    def __init__(self,
                 depth: Tuple[float, float] = (2.0, 10.0),
                 width: Tuple[float, float] = (1.0, 10.0),
                 height: Tuple[float, float] = (2.0, 5.0),
                 absorption: Tuple[float, float] = (0.2, 0.9),
                 # noise_from: Optional[Union[str, List[str]]] = None,
                 # snr: Tuple[float, float] = (5.0, 15.0),
                 ):

        super().__init__()
        self.depth = depth
        self.width = width
        self.height = height
        self.absorption = absorption
        self.max_order_ = 17

    @staticmethod
    def random(m: float, M: float):
        return (M - m) * np.random.random_sample() + m

    def __call__(self,
                 original: np.ndarray,
                 sample_rate: int) -> np.ndarray:

        original = normalize(original).squeeze(axis=None)
        n_samples = len(original)

        # generate a room at random
        depth = self.random(*self.depth)
        width = self.random(*self.width)
        height = self.random(*self.height)
        absorption = self.random(*self.absorption)
        room = pra.ShoeBox([depth, width, height],
                           fs=sample_rate,
                           absorption=absorption,
                           max_order=self.max_order_)

        # play the original audio chunk at a random location within the room
        source = [self.random(0, depth),
                  self.random(0, width),
                  self.random(0, height)]
        room.add_source(source, signal=original, delay=0.)

        # place the microphone at a random location within the room
        microphone = [self.random(0, depth),
                      self.random(0, width),
                      self.random(0, height)]
        room.add_microphone_array(
            pra.MicrophoneArray(np.c_[microphone, microphone], sample_rate))

        # create the Room Impulse Response (RIR)
        room.compute_rir()

        # simulate sound propagation
        room.simulate()

        return room.mic_array.signals[0,:n_samples, np.newaxis]
