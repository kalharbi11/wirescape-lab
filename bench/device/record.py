# SPDX-License-Identifier: GPL-3.0-only
"""Owner-authorized capture; never invoked in a dry-run or CI."""
import platform
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path


class Recorder:
    def __init__(self, mode, directory, rate=48000, input_device=None,
                 monitor_target=None, process_helper=None, engine_pid=None):
        self.mode=mode
        self.directory=Path(directory)
        self.rate=rate
        self.input_device=input_device
        self.monitor_target=monitor_target
        self.process_helper=process_helper
        self.engine_pid=engine_pid
        self.proc=None
        self.temp=None
        self.stream=None
        self.blocks=[]
        self.started=None
        self.file=self.directory/"capture.flac"

    def start(self):
        if self.mode=="none":return
        if self.mode=="input":
            import sounddevice as sd
            def capture(samples, frames, timestamp, status):
                self.blocks.append(samples.copy())
            self.stream=sd.InputStream(samplerate=self.rate,channels=2,dtype="float32",
                                       device=self.input_device,callback=capture)
            self.stream.start()
        elif self.mode=="monitor":
            self.temp=Path(tempfile.mkstemp(suffix=".wav",dir=self.directory)[1])
            if shutil.which("pw-record"):
                cmd=["pw-record","--rate",str(self.rate),"--channels","2"]
                if self.monitor_target:cmd+=["--target",self.monitor_target]
                cmd+=[str(self.temp)]
            elif shutil.which("parec"):
                if not self.monitor_target:
                    raise RuntimeError("parec requires --monitor-target (sink.monitor)")
                self.temp.unlink(missing_ok=True)
                self.temp=self.temp.with_suffix(".raw")
                cmd=["parec","--device",self.monitor_target,"--format=s16le",
                     "--rate",str(self.rate),"--channels=2"]
            else:
                raise RuntimeError("install pw-record or parec for monitor capture")
            stream=self.temp.open("wb") if self.temp.suffix==".raw" else subprocess.DEVNULL
            self.proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.PIPE)
            if stream!=subprocess.DEVNULL:stream.close()
            if self.proc.poll() is not None:
                raise RuntimeError("monitor recorder exited before starting")
        elif self.mode=="process-loopback":
            if platform.system()!="Windows":
                raise RuntimeError("process-loopback capture requires Windows")
            if not self.process_helper or not Path(self.process_helper).is_file():
                raise RuntimeError("process-loopback requires compatible --process-helper; see OWNER_RUN.md")
            if not self.engine_pid:
                raise RuntimeError("process-loopback requires the engine PID")
            self.temp=self.directory/"process-loopback.wav"
            self.proc=subprocess.Popen([str(self.process_helper),"--confirm-audio",
                                        "--pid",str(self.engine_pid),"--rate",str(self.rate),
                                        "--out",str(self.temp)],
                                       stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            if self.proc.poll() is not None:
                raise RuntimeError("process-loopback recorder exited before starting")
        else:
            raise ValueError("unsupported recording mode")
        self.started=time.monotonic()

    def stop(self):
        if self.mode=="none" or self.started is None:return None
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            import numpy as np
            samples=np.concatenate(self.blocks,axis=0) if self.blocks else np.zeros((0,2),"float32")
        else:
            if self.proc.poll() is None:
                if platform.system()=="Windows":self.proc.terminate()
                else:self.proc.send_signal(signal.SIGINT)
                try:self.proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait()
            if not self.temp or not self.temp.is_file():
                raise RuntimeError("recorder did not produce a file")
            import numpy as np
            import soundfile as sf
            if self.temp.suffix==".raw":
                samples=np.fromfile(self.temp,"<i2")
                samples=samples[:len(samples)//2*2].reshape(-1,2).astype("float32")/32768
            else:
                samples,source_rate=sf.read(self.temp,dtype="float32",always_2d=True)
                if source_rate!=self.rate:
                    raise RuntimeError("recording sample rate differs from requested rate")
            self.temp.unlink(missing_ok=True)
        if not len(samples):
            raise RuntimeError("capture contained no samples")
        import soundfile as sf
        sf.write(self.file,samples,self.rate,format="FLAC",subtype="PCM_24")
        return self.file
