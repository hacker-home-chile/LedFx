"""Regression tests against actual FIFO reads, including split stereo samples."""
import os
import struct
import tempfile
import threading
import time
import unittest

import numpy as np
from ledfx.effects.audio import FIFOAudioStream


class FifoCadenceTest(unittest.TestCase):
    def run_stream(self, blocks, writer):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + '/audio'
            os.mkfifo(path)
            callbacks = []
            done = threading.Event()
            def callback(samples, *_):
                callbacks.append((time.monotonic(), samples.copy()))
                if len(callbacks) == blocks:
                    stream.stop()
                    done.set()
            stream = FIFOAudioStream(callback)
            stream.FIFO_PATH = path
            def produce():
                with open(path, 'wb', buffering=0) as f:
                    writer(f)
            stream.start()
            producer = threading.Thread(target=produce, daemon=True)
            producer.start()
            try:
                self.assertTrue(done.wait(4), 'FIFO did not produce complete analysis blocks')
            finally:
                stream.close()
                producer.join(2)
            self.assertEqual(len(callbacks), blocks)
            return callbacks

    def test_fragments_preserve_all_samples(self):
        values = list(range(1470))
        data = b''.join(struct.pack('<hh', n, n) for n in values)
        def writer(f):
            pos = 0
            for size in [1, 7, 1200, 17, 300, 13, 2048, 5, 2289]:
                f.write(data[pos:pos+size])
                pos += size
                time.sleep(.001)
            if pos < len(data):
                f.write(data[pos:])
        callbacks = self.run_stream(2, writer)
        self.assertEqual([len(s) for _, s in callbacks], [735, 735])
        np.testing.assert_allclose(np.concatenate([s for _, s in callbacks]), np.array(values)/32767, atol=1e-6)

    def test_fifty_ms_bursts_are_paced_at_sixty_hz(self):
        def writer(f):
            deadline = time.monotonic()
            for _ in range(4):
                time.sleep(max(0, deadline-time.monotonic()))
                f.write(struct.pack('<hh', 100, 100) * 2205)
                deadline += .05
        callbacks = self.run_stream(12, writer)
        gaps = [b[0]-a[0] for a,b in zip(callbacks, callbacks[1:])]
        self.assertGreater(min(gaps), .008, 'analysis callbacks arrived as a burst')
        self.assertGreater(callbacks[-1][0]-callbacks[0][0], .16)
        self.assertTrue(all(len(samples)==735 for _,samples in callbacks))


if __name__ == '__main__':
    unittest.main()
