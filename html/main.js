const signalingUrl = 'wss://ayame-labo.shiguredo.jp/signaling';
let roomId = 'zenithfull@mini4-room';
let clientId = 'mini4-client';
let videoCodec = 'H264';
let audioCodec = null;
let signalingKey = 'Nlqlm3fKd-ABK5IPoM0LS3pSPgu0DB8o_vNqB1OOahbRn634';

function onChangeVideoCodec() {
//  videoCodec = document.getElementById("video-codec").value;
//  if (videoCodec == 'none') {
//    videoCodec = null;
//  }
}
// query string から roomId, clientId を取得するヘルパー
function parseQueryString() {
  const qs = window.Qs;
  if (window.location.search.length > 0) {
    var params = qs.parse(window.location.search.substr(1));
    if (params.roomId) {
      roomId = params.roomId;
    }
    if (params.clientId) {
      clientId = params.clientId;
    }
    if (params.signalingKey) {
      signalingKey = params.signalingKey;
    }
  }
}


// parseQueryString();

const roomIdInput = document.getElementById("roomIdInput");
// roomIdInput.addEventListener('change', (event) => {
//   console.log(event);
//   roomId = event.target.value;
// });

