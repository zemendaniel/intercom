import asyncio
from fractions import Fraction
import sounddevice as sd
import numpy as np
from aiortc import RTCPeerConnection, RTCIceServer, RTCConfiguration, RTCSessionDescription, MediaStreamTrack, \
    MediaStreamError
from aiortc.contrib.media import MediaRelay, MediaPlayer
from av.audio import AudioFrame
from find_device import get_output_device_by_name, get_input_device_by_name


class AudioPlaybackTrack:
    def __init__(self, track, device):
        self.track = track
        self.queue = asyncio.Queue(maxsize=20)
        self.device = device
        self.buffer = np.empty((0, 2), dtype=np.int16)

        print(f"[AudioPlaybackTrack] Starting output stream on device {self.device}")
        try:
            self.stream = sd.OutputStream(
                samplerate=48000,
                channels=2,
                dtype='int16',
                blocksize=256,
                device=self.device,
                callback=self._callback,
            )
            self.stream.start()
        except sd.PortAudioError as e:
            pass
            print(f"PortAudio error opening output stream: {e}")

        self._task_receive = asyncio.create_task(self._receive_audio())

    async def _receive_audio(self):
        print("[AudioPlaybackTrack] Audio receive task started")
        while True:
            try:
                frame = await self.track.recv()
                # print("[AudioPlaybackTrack] Received audio frame")
            except MediaStreamError:
                # print("[AudioPlaybackTrack] Track ended or closed")
                break

            try:
                self.queue.put_nowait(frame)
                # print(f"[AudioPlaybackTrack] Frame put in queue (size={self.queue.qsize()})")
            except asyncio.QueueFull:
                pass
                # print("[AudioPlaybackTrack] Queue full, dropping frame")

    def _callback(self, outdata, frames, time, status):
        if status:
            pass
            # print(f"[AudioPlaybackTrack] Output stream status: {status}")

        try:
            while self.buffer.shape[0] < frames:
                frame = self.queue.get_nowait()
                raw = frame.to_ndarray()
                data = raw.reshape(-1, 2)  # reshape to (samples, 2 channels)
                if data.dtype != np.int16:
                    data = (data * 32767).astype(np.int16)
                self.buffer = np.vstack([self.buffer, data])
                # print(f"[AudioPlaybackTrack] Added {data.shape[0]} samples to buffer (buffer size={self.buffer.shape[0]})")

        except asyncio.QueueEmpty:
            pass
            # print("[AudioPlaybackTrack] Queue empty, no new data to add")

        if self.buffer.shape[0] >= frames:
            outdata[:] = self.buffer[:frames]
            self.buffer = self.buffer[frames:]
            # print(f"[AudioPlaybackTrack] Outputting {frames} frames, buffer left {self.buffer.shape[0]}")
        else:
            outdata.fill(0)  # not enough data, output silence
            self.buffer = np.empty((0, 2), dtype=np.int16)
            # print(f"[AudioPlaybackTrack] Not enough data, outputting silence")

    async def close(self):
        if self.stream:
            print("[AudioPlaybackTrack] Stopping output stream")
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if self._task_receive:
                self._task_receive.cancel()
                try:
                    await self._task_receive
                except asyncio.CancelledError:
                    pass
                self._task_receive = None


class AudioRecordTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, mic_url, samplerate=48000, channels=1, blocksize=256):
        super().__init__()
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.queue = asyncio.Queue(maxsize=10)
        self.frame_count = 0
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            blocksize=self.blocksize,
            dtype='int16',
            device=mic_url,
        )
        self.stream.start()
        self._produce_task = asyncio.create_task(self._produce_audio())

    async def _produce_audio(self):
        try:
            while True:
                if self.stream is None:
                    print("AudioRecordTrack stream is None, stopping _produce_audio task")
                    break

                data, overflow = await asyncio.to_thread(self.stream.read, self.blocksize)
                if overflow:
                    continue

                try:
                    await self.queue.put(data.copy())
                except asyncio.QueueFull:
                    try:
                        _ = self.queue.get_nowait()
                        await self.queue.put(data.copy())
                    except asyncio.QueueEmpty:
                        pass
        except asyncio.CancelledError:
            print("AudioRecordTrack _produce_audio task cancelled")
            # Cleanup if needed
            pass

    async def recv(self):
        data = await self.queue.get()
        frame = AudioFrame(format="s16", layout="mono", samples=data.shape[0])
        frame.planes[0].update(data.tobytes())
        frame.sample_rate = self.samplerate
        frame.time_base = Fraction(1, self.samplerate)
        frame.pts = self.frame_count
        self.frame_count += frame.samples
        return frame

    async def close(self):
        # Cancel the _produce_audio task and wait for it to finish
        if self._produce_task:
            self._produce_task.cancel()
            try:
                await self._produce_task
            except asyncio.CancelledError:
                pass
            self._produce_task = None

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class MediaCapture:
    def __init__(self, cam_url, mic_name, playback_name):
        self.cam_url = cam_url
        self.fps = 30
        self.width = 1280
        self.height = 720
        self.mic_index = get_input_device_by_name(mic_name)
        self.playback_index = get_output_device_by_name(playback_name)
        self.pcs = set()
        self.playback_track = None

        self.cam_relay = None
        self.cam = None
        self.mic_relay = None
        self.mic = None

        self.is_running = False

    def _create_tracks(self):
        if self.is_running:
            return self.cam_relay.subscribe(self.cam.video), self.mic_relay.subscribe(self.mic)

        if self.cam_relay is None:
            self.cam = MediaPlayer(
                self.cam_url,
                format="v4l2",
                options={"framerate": str(self.fps), "video_size": f"{self.width}x{self.height}"}
            )
            self.cam_relay = MediaRelay()

        self.is_running = True

        if self.mic_relay is None:
            self.mic = AudioRecordTrack(self.mic_index)
            self.mic_relay = MediaRelay()

        audio_track = self.mic_relay.subscribe(self.mic)
        video_track = self.cam_relay.subscribe(self.cam.video)

        return video_track, audio_track


    async def handle_offer(self, params):
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        config = RTCConfiguration(iceServers=[
            RTCIceServer(urls=["turn:10.21.40.25:3478"], username="turnuser", credential="turnpassword")
        ])
        pc = RTCPeerConnection(configuration=config)
        self.pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is", pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)

        @pc.on("track")
        def on_track(track):
            if track.kind == "audio":
                print("Client audio track received")
                if not self.playback_track:
                    self.playback_track = AudioPlaybackTrack(track, self.playback_index)

        video, audio = self._create_tracks()
        if video:
            pc.addTrack(video)
        if audio:
            pc.addTrack(audio)

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return pc.localDescription.sdp, pc.localDescription.type

    async def shutdown(self):
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()

        if self.playback_track:
            await self.playback_track.close()
            self.playback_track = None

        if self.cam:
            self.cam.video.stop()
            self.cam = None
            self.cam_relay = None

        if self.mic:
            await self.mic.close()
            self.mic = None
            self.mic_relay = None

        self.is_running = False
