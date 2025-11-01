let pc = null;
const video = document.getElementById('video');
const audio = document.getElementById('audio');
let localAudioTrack = null;



function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    console.log("Creating offer...");
    return pc.createOffer().then((offer) => {
        console.log("Setting local description...");
        return pc.setLocalDescription(offer);
    }).then(() => {
        console.log("Waiting for ICE gathering to complete...");
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                console.log("ICE already complete");
                resolve();
            } else {
                const timeout = setTimeout(() => {
                    pc.removeEventListener('icegatheringstatechange', checkState);
                    resolve();
                }, 100);

                const checkState = () => {
                    console.log(pc.iceGatheringState);
                    if (pc.iceGatheringState === 'complete') {
                        clearTimeout(timeout);
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        console.log("ICE gathering complete");
                        resolve();
                    }
                };

                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        console.log("Sending offer to server...");
        let offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then((response) => {
        console.log("Received answer from server");
        return response.json();
    }).then((answer) => {
        console.log("Setting remote description...");
        return pc.setRemoteDescription(answer);
    }).catch((e) => {
        console.error("Negotiation failed:", e);
        alert(e);
    });
}

function start() {
    document.getElementById('start').style.display = 'none';
    let config = {
        sdpSemantics: 'unified-plan',
        iceServers: [{
            urls: ['turn:{{ turn_url }}'],
            username: '{{ turn_user }}',
            credential: '{{ turn_password }}'
        }]
    };

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', (evt) => {
        if (evt.track.kind == 'video') {
            video.srcObject = evt.streams[0];
        } else {
            audio.srcObject = evt.streams[0];
        }
    });

    navigator.mediaDevices.getUserMedia({ audio: true, video: false }).then((stream) => {
        stream.getTracks().forEach((track) => {
            if (track.kind === 'audio') {
                localAudioTrack = track;
                track.enabled = false;
            }
            pc.addTrack(track, stream);
        });

        negotiate();
        document.getElementById('media').style.display = 'inline-block';

    }).catch((err) => {
        console.error("getUserMedia error:", err);
    });
}

function stop() {
    document.getElementById('media').style.display = 'none';

    // close peer connection
    if (pc !== null) {
        setTimeout(() => {
            pc.close();
        }, 500);


        fetch("/stop", {
              method: "POST"
            }).then(response => {
              if (response.ok) {
                console.log("Server shutdown requested");
              } else {
                console.error("Shutdown request failed");
              }
            });
    }
    document.getElementById('start').style.display = 'inline-block';
    if (!video.muted) {
        toggleAudio();
    }
    if (localAudioTrack.enabled) {
        toggleMic();
    }
    localAudioTrack.stop();
}

function toggleMic() {
    if (localAudioTrack !== null) {
        localAudioTrack.enabled = !localAudioTrack.enabled;
        document.getElementById('mic-control').innerHTML = localAudioTrack.enabled ?
            '<i class="fa-solid fa-microphone"></i>' :
            '<i class="fa-solid fa-microphone-slash"></i>';
    }
}
function toggleAudio() {
    video.muted = !video.muted;
    audio.muted = !audio.muted;
    document.getElementById('audio-control').innerHTML = video.muted ?
        '<i class="fa-solid fa-volume-xmark"></i>' :
        '<i class="fa-solid fa-volume-high"></i>';
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        video.requestFullscreen().catch(err => {
            alert(`Error attempting to enable fullscreen: ${err.message}`);
        });
        video.controls = false;
    } else {
        document.exitFullscreen();
    }
}
