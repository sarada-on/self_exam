document.getElementById('fileButton').addEventListener('click', function() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'text/plain';
    
    fileInput.onchange = function(event) {
        const file = event.target.files[0];
        if (file) {
    		if (!file.name.endsWith(".txt")) {
				alert("TXT 파일만 업로드 가능합니다!");
				return;
			};
        	
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview').textContent = e.target.result;
                document.getElementById('filename').value = file.name.replace(/\.[^/.]+$/, "");
            };
            reader.readAsText(file);
        }
    };
    
    fileInput.click();
});

document.getElementById("pasteButton").addEventListener("click", function() {
    navigator.clipboard.readText().then(function(text) {
        document.getElementById("preview").textContent = text;
    }).catch(function(err) {
        console.error("Failed to read clipboard contents: ", err);
    });
});

document.getElementById("uploadButton").addEventListener("click", function(e) {
	e.preventDefault();
    uploadFile(overwrite = false);
});

function uploadFile(overwrite = false) {
	if (!document.getElementById('preview').textContent) {
		alert("먼저 파일을 선택하거나 클립보드를 통해 텍스트파일을 붙여넣기 하세요!");
		return;
	}
	if (!document.getElementById('filename').value) {
		alert("저장할 시험명을 입력하세요!");
		return;
	}
	
	let exam_type = document.getElementById('filename').value;
	let url = `/upload/${encodeURIComponent(exam_type)}/${overwrite}`;
	
	let fileContent = document.getElementById('preview').textContent;
	fileContent = fileContent.replace(/(\r\n|\n|\r)/g, '\n');			
	fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "text/plain"
		},
		body: fileContent
	})
	.then(response => response.json())
	.then(data => {
		if (data.ask_overwrite) {
			if (confirm("동일한 파일이 존재합니다. 덮어쓰시겠습니까?")) {
				uploadFile(true);  // 덮어쓰기 확인 후 다시 업로드 요청                    
			}
			return;
		} 	
		alert(data.msg_txt);
		if (data.is_saved) {					
			location.href = "/";				
		}
	})
	.catch(error => console.error("업로드 실패:", error));
}
