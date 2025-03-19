let currentQuestionIndex = 0;
let questions = [];
let isAnswerChecked = false;
let isExamEnded = false;
let score = 0; // 맞힌 문제 수
let wrongAnswers = []; // 틀린 문제 목록

// 배열을 랜덤하게 섞는 함수
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

// 문제 표시 함수
function displayQuestion() {		
    const question = questions[currentQuestionIndex];
    const questionContainer = document.getElementById("question-container");
    const progress = document.getElementById("progress");

    const options = question.item.map((item, index) => ({ label: String.fromCharCode(65 + index), item }));
    const shuffledOptions = shuffleArray([...options]);

    questionContainer.innerHTML = `
        <h5>${question.question}</h5>
        ${shuffledOptions.map((option, index) => `
            <label>
                <input type="checkbox" name="answer" value="${String.fromCharCode(65 + index)}">
                ${String.fromCharCode(65 + index)}. ${option.item.slice(2).trim().replace(/\\n/g, '<br/>&emsp;&emsp;&emsp;')}
            </label><br>
        `).join('')}
    `;

    progress.innerHTML = `문제 ${currentQuestionIndex + 1} / ${questions.length}`;
    
    // 원래 보기와 섞은 보기를 매핑
    question.optionMap = {};
    shuffledOptions.forEach((option, index) => {
        question.optionMap[option.item] = { label: String.fromCharCode(65 + index), text: option.item.slice(2) };
    });       
    
    isAnswerChecked = false;
	document.getElementById("answer-feedback").innerHTML = "";
	document.getElementById("submit").disabled = false;
}

// 정답 확인 함수
function checkAnswer() {
    const selectedAnswers = Array.from(document.querySelectorAll('input[name="answer"]:checked'))
        .map(input => input.value);

    const question = questions[currentQuestionIndex];

    const correctAnswers = question.answer.map(answer => {
        const originalOption = question.item.find(item => item.startsWith(answer));
        return question.optionMap[originalOption].label;
    });

    const feedback = document.getElementById("answer-feedback");

    if (JSON.stringify(selectedAnswers.sort()) === JSON.stringify(correctAnswers.sort())) {
        feedback.innerHTML = "정답입니다!";
        feedback.style.color = "green";
        score++; // 점수 증가
    } else {
        feedback.innerHTML = `오답입니다. 정답은: ${correctAnswers.join(', ')}`;
        feedback.style.color = "red";

        // 틀린 문제 저장
        wrongAnswers.push({
            question: question.question,
            correctAnswer: correctAnswers.map(label => {
            	return `${label}. ${Object.values(question.optionMap).find(opt => opt.label === label).text.replace(/\\n/g, '<br/>&emsp;')}`; 
            	}).join(`<br/>`)
        });
    }
	
	isAnswerChecked = true;
	document.getElementById("submit").disabled = true;
}

// 다음 문제 함수
function nextQuestion() {
	if (!isExamEnded) { 
	    if (!isAnswerChecked) {
	        const feedback = document.getElementById("answer-feedback");
	        feedback.innerHTML = "정답 확인을 눌러야 다음 문제로 넘어갈 수 있습니다!";
	        feedback.style.color = "red";
	        return;
	    }
	
	    currentQuestionIndex++;
	    if (currentQuestionIndex < questions.length) {
	        displayQuestion();
	    } else {
	        showResult(); // 시험 종료 시 결과 표시
	    }
	} else {
		location.href = '/';
	}
}

// 결과 화면 표시 함수
function showResult() {
    const questionContainer = document.getElementById("question-container");
    const scorePercentage = ((score / questions.length) * 100).toFixed(2);

    let resultHTML = `<h4>총 점수 : ${score} / ${questions.length} (${scorePercentage}%)</h4>`;
    
    if (wrongAnswers.length > 0) {
        resultHTML += `<h5>틀린 문제</h5><ul>`;
        wrongAnswers.forEach(wrong => {
            resultHTML += `<li><b>${wrong.question}</b><br>${wrong.correctAnswer}</li>`;
        });
        resultHTML += `</ul>`;
    } else {
        resultHTML += `<p>완벽하네요! 모든 문제를 맞혔어요!</p>`;
    }

    questionContainer.innerHTML = resultHTML;
    isExamEnded = true;
    
    document.getElementById("answer-feedback").innerHTML = "";
    document.getElementById("submit").disabled = false;
    document.getElementById("submit").style.display = 'none';
    document.getElementById("next").innerHTML = '다른 시험 보기';
}

// 문제 로드 함수
function loadQuestions(examType) {
    fetch(`/exam/${examType}/json`)
        .then(response => response.json())
        .then(data => {
            questions = shuffleArray(data);
            displayQuestion();
            hideLoading();
            document.getElementById("submit").disabled = false;
            document.getElementById("next").disabled = false;
        });
}

// URL에서 examType을 추출하여 시험 문제 로드
const urlPath = window.location.pathname.split('/');
const examType = urlPath[urlPath.length - 1];
document.getElementById("exam-title").textContent = `${decodeURIComponent(examType)}`;
loadQuestions(examType);

// 이벤트 리스너
document.getElementById("submit").addEventListener("click", checkAnswer);
document.getElementById("next").addEventListener("click", nextQuestion);
