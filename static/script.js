function showLoading(msg_text) {
	document.getElementById("loading-screen").style.display = "flex";
	if ( msg_text != '' ) {
		document.getElementById("loading_text").innerHTML = msg_text;
	}
}
		
function hideLoading() {
	document.getElementById("loading-screen").style.display = "none";
}

function showLoginProgress() {
	showLoading('사용자 인증 처리 중입니다. 잠시만 기다려주세요.');
}
