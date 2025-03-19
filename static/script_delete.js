let sortDirection = {};  // 정렬 상태 저장

function sortTable(columnIndex) {
	let table = document.getElementById("sortableTable");
	let tbody = table.querySelector("tbody");
	let rows = Array.from(tbody.rows);

	// 현재 정렬 방향 확인 및 변경
	let isAscending = sortDirection[columnIndex] = !sortDirection[columnIndex];

	rows.sort((rowA, rowB) => {
		let cellA = rowA.cells[columnIndex].textContent.trim();
		let cellB = rowB.cells[columnIndex].textContent.trim();

		// 숫자인 경우 비교 방식 변경
		if (!isNaN(cellA) && !isNaN(cellB)) {
			return isAscending ? cellA - cellB : cellB - cellA;
		}

		return isAscending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
	});

	// 기존 행 제거 후 재배치
	tbody.innerHTML = "";
	rows.forEach(row => tbody.appendChild(row));

	// 정렬 아이콘 업데이트
	updateSortIcons(columnIndex, isAscending);
}

function updateSortIcons(columnIndex, isAscending) {
	let headers = document.querySelectorAll("#sortableTable th");
	headers.forEach((header, index) => {
		let icon = header.querySelector(".sort-icon");
		if (index === columnIndex) {
			icon.textContent = isAscending ? "▲" : "▼";
		} else {
			icon.textContent = "";  // 다른 컬럼 아이콘 초기화
		}
	});
}

function deleteFile(exam_type) {	
	if (!confirm("삭제 하시겠습니까?")) {
		return;
	}
	let url = `/delete/${encodeURIComponent(exam_type)}`;
	
	fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "text/plain"
		},
		body: ""
	})
	.then(response => response.json())
	.then(data => {		
		alert(data.msg_txt);
		if (data.is_deleted) {					
			location.href = "/delete";				
		}				
	})
	.catch(error => console.error("삭제 실패:", error));
}

sortTable(0);
