# SPDX-License-Identifier: GPL-3.0-only
"""Authorized owner recording. No recorder is instantiated during a dry run."""
import platform
import os
import queue
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path


class Recorder:
    def __init__(self,mode,directory,rate=48000,input_device=None,
                 monitor_target=None,process_helper=None,engine_pid=None):
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
        self.started=None
        self.file=self.directory/"capture.flac"
        self.queue=None
        self.writer=None
        self.write_error=None
        self.overruns=0

    def _start_input(self):
        import sounddevice as sd
        import soundfile as sf
        self.queue=queue.Queue(maxsize=64)
        self.flac=sf.SoundFile(str(self.file),mode="w",samplerate=self.rate,
                               channels=2,format="FLAC",subtype="PCM_24")
        def write():
            try:
                while True:
                    block=self.queue.get()
                    if block is None:break
                    self.flac.write(block)
            except Exception as exc:
                self.write_error=exc
            finally:
                self.flac.close()
        self.writer=threading.Thread(target=write,daemon=True)
        self.writer.start()
        def capture(samples,frames,timestamp,status):
            try:self.queue.put_nowait(samples.copy())
            except queue.Full:self.overruns+=1
        self.stream=sd.InputStream(samplerate=self.rate,channels=2,
                                   dtype="float32",device=self.input_device,callback=capture)
        self.stream.start()

    def start(self):
        if self.mode=="none":return
        if self.mode=="input":
            self._start_input()
        elif self.mode=="monitor":
            # Target is chosen explicitly; no microphone or endpoint-mix fallback.
            fd,name=tempfile.mkstemp(suffix=".wav",dir=self.directory)
            os.close(fd)
            self.temp=Path(name)
            self.temp.unlink()  # pw-record creates its own output; avoid inherited fd
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
            try:
                self.proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.DEVNULL)
            finally:
                if stream!=subprocess.DEVNULL:stream.close()
            if self.proc.poll() is not None:
                raise RuntimeError("monitor recorder exited before starting")
        elif self.mode=="process-loopback":
            if platform.system()!="Windows":
                raise RuntimeError("process-loopback capture requires Windows")
            if not self.process_helper or not Path(self.process_helper).is_file():
                raise RuntimeError("process-loopback requires --process-helper capture_engine.exe")
            if not self.engine_pid:
                raise RuntimeError("process-loopback requires the engine PID")
            self.temp=self.directory/"process-loopback.wav"
            self.proc=subprocess.Popen([str(self.process_helper),"--confirm-audio",
                                        "--pid",str(self.engine_pid),"--rate",str(self.rate),
                                        "--out",str(self.temp)],
                                       stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE)
            if self.proc.poll() is not None:
                raise RuntimeError("process-loopback recorder exited before starting")
        else:
            raise ValueError("unsupported recording mode")
        self.started=time.monotonic()

    def _stop_proc(self):
        if not self.proc:return
        if self.mode=="process-loopback":
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()  # helper detects stdin EOF, finalizes WAV
            try:
                code=self.proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
                raise RuntimeError("process-loopback helper did not finish its recording")
            if code!=0:
                error=(self.proc.stderr.read() if self.proc.stderr else b"").decode("utf-8",errors="replace")
                raise RuntimeError("process-loopback helper failed: "+error[:300])
        elif self.proc.poll() is None:
            if platform.system()=="Windows":self.proc.terminate()
            else:self.proc.send_signal(signal.SIGINT)
            try:self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
                raise RuntimeError("monitor recorder did not stop")

    def stop(self):
        if self.mode=="none" or self.started is None:return None
        self.started=None
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            # Shutdown follows callback stop; no new blocks are pushed.
            self.queue.put(None)
            self.writer.join(timeout=15)
            if self.writer.is_alive():
                raise RuntimeError("input FLAC writer stalled")
            if self.write_error:raise RuntimeError("input FLAC writer: "+str(self.write_error))
            if self.overruns:raise RuntimeError(f"input capture lost {self.overruns} blocks")
        else:
            self._stop_proc()
            if not self.temp or not self.temp.is_file():
                raise RuntimeError("recorder did not produce a file")
            import soundfile as sf
            import numpy as np
            if self.temp.suffix==".raw":
                with sf.SoundFile(str(self.file),mode="w",samplerate=self.rate,
                                  channels=2,format="FLAC",subtype="PCM_24") as dest:
                    with self.temp.open("rb") as src:
                        while chunk:=src.read(2*2*65536):
                            frames=np.frombuffer(chunk[:len(chunk)//4*4],dtype="<i2").reshape(-1,2)
                            dest.write(frames.astype("float32")/32768.)
            else:
                with sf.SoundFile(str(self.temp),"r") as src:
                    if src.samplerate!=self.rate or src.channels!=2:
                        raise RuntimeError("recording format mismatch")
                    with sf.SoundFile(str(self.file),mode="w",samplerate=self.rate,
                                      channels=2,format="FLAC",subtype="PCM_24") as dest:
                        while True:
                            frames=src.read(65536,dtype="float32",always_2d=True)
                            if not len(frames):break
                            dest.write(frames)
            self.temp.unlink(missing_ok=True)
        if not self.file.is_file() or self.file.stat().st_size<=100:
            raise RuntimeError("capture contained no audio frames")
        return self.file
