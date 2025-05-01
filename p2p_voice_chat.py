# The following implementation assumes aiortc is available.
# If you encounter `ModuleNotFoundError`, install it via: pip install aiortc

import asyncio
import json
from aiohttp import web

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
except ModuleNotFoundError:
    raise ImportError("The 'aiortc' module is not installed. Please run 'pip install aiortc' and try again.")

pcs = set()


def create_media():
    player = MediaPlayer('default', format='dshow')
    recorder = MediaRecorder('default', format='dshow')
    return player, recorder


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)
    player, recorder = create_media()

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            recorder.addTrack(track)

    if player.audio:
        for t in player.audio:
            pc.addTrack(t)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    await recorder.start()

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_post("/offer", offer)

if __name__ == "__main__":
    web.run_app(app, port=8080)
