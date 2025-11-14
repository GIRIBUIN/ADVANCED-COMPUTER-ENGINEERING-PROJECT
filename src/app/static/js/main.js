// script.js

// 템플릿 데이터: 분석 모델이 반환했다고 가정하는 JSON 데이터
const MOCK_ANALYSIS_RESULT = {
    product_name: "삼성 갤럭시 S24 Ultra",
    keyword: "용량",
    rating: "4.3/5.0",
    positive_summary: [
        "카메라 성능이 전작 대비 크게 향상되었습니다.",
        "5배 기능이 더욱 정교해졌고 반응속도가 빨라졌습니다.",
        "배터리 지속시간이 하루 종일 사용하기에 충분합니다.",
        "디스플레이 품질이 매우 뛰어나고 밝기도 충분합니다."
    ],
    negative_summary: [
        "크기가 커서 한 손 사용이 어렵다는 의견",
        "발열이 간혹 발생한다는 리뷰"
    ]
};

// 현재 대화 시퀀스 상태를 저장하는 변수
let currentStep = 1; // 1: 초기, 2: 링크 입력 후, 3: 키워드 입력 후

document.addEventListener('DOMContentLoaded', () => {
    // 2. 시스템 메시지 (링크 입력 요구) 출력
    addMessage('system', '안녕하세요! 제품 리뷰 분석기입니다. 분석하고 싶은 제품의 링크를 입력해 주세요.');

    document.querySelector('.send-button').addEventListener('click', handleUserInput);
    document.querySelector('.text-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleUserInput();
        }
    });
});


// 사용자 입력 처리 및 시퀀스 진행 함수
function handleUserInput() {
    const inputField = document.querySelector('.text-input');
    const inputContent = inputField.value.trim();

    if (inputContent === '') return;

    // 사용자 입력 메시지 출력
    addMessage('user', inputContent);
    inputField.value = ''; // 입력창 초기화

    // 시퀀스 분기 처리
    if (currentStep === 1) {
        // 3. 사용자 링크 입력 완료
        // 4. 시스템 메시지 (키워드 입력 요구) 출력
        addMessage('system', '링크를 확인했습니다. 분석을 원하시는 **주요 키워드**를 입력해 주세요. (예: 배터리, 카메라, 디자인)');
        currentStep = 2;
        document.querySelector('.tip-box p').textContent = 'Tip: 키워드를 입력하고 전송 버튼을 눌러주세요.';
    } else if (currentStep === 2) {
        // 4. 사용자 키워드 입력 완료
        
        // 5. 크롤링 & 6. 전처리 & 7. AI 분석 시뮬레이션
        simulateAnalysisProcess(inputContent);
        currentStep = 3;
        document.querySelector('.tip-box p').textContent = 'Tip: 제품 링크를 입력하면 키워드 입력창이 나타납니다';
    } else if (currentStep === 3) {
        // 8. 분석 결과 출력 후 추가 대화 (저장 질문 등에 대한 응답 처리)
        // 현재는 시퀀스 완료로 간주하고 초기화
        addMessage('system', `"${inputContent}"에 대한 추가 액션은 구현되지 않았습니다. 새로운 분석을 시작하려면 페이지를 새로고침 해주세요.`);
        currentStep = 0; // 시퀀스 종료
    }
}

// 분석 과정 시뮬레이션 함수
function simulateAnalysisProcess(keyword) {
    // 5초 지연 후 최종 결과 출력 (분석 작업 시뮬레이션)
    addMessage('system', `입력하신 키워드 **"${keyword}"**를 중심으로 리뷰를 크롤링 및 분석 중입니다. 잠시만 기다려 주세요...`);
    
    // 로딩 시뮬레이션을 위한 임시 메시지 (UX 개선)
    const loadingMsg = addMessage('system', '처리 중... (크롤링, 전처리, 분석)', true);

    setTimeout(() => {
        // 로딩 메시지 제거
        if (loadingMsg) loadingMsg.remove();
        
        // 8. 시스템 메시지 출력 (JSON 데이터를 이용한 친화적인 폼)
        const mockResult = { ...MOCK_ANALYSIS_RESULT, keyword: keyword };
        const resultHtml = generateResultHtml(mockResult);
        addMessage('result', resultHtml);

    }, 3000); // 3초 지연
}

// 새로운 메시지를 채팅 영역에 추가하는 함수
function addMessage(type, content, isTemporary = false) {
    const chatArea = document.querySelector('.chat-area');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    
    // 메시지 유형에 따른 클래스 및 내용 설정
    if (type === 'user') {
        messageDiv.classList.add('user-message');
        messageDiv.innerHTML = `<div class="link-bubble">${content}</div>`;
    } else if (type === 'system') {
        messageDiv.classList.add('system-message');
        messageDiv.innerHTML = `<p>${content}</p>`;
    } else if (type === 'result') {
        messageDiv.classList.add('system-message', 'analysis-result-box');
        messageDiv.innerHTML = content; 
    }

    // 시간표시 추가
    const now = new Date();
    const timeString = `오후 ${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
    messageDiv.innerHTML += `<span class="timestamp">${timeString}</span>`;

    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight; 

    if (isTemporary) {
        return messageDiv; // 임시 메시지일 경우 DOM 요소를 반환하여 나중에 제거할 수 있도록 함
    }
    return null;
}

// JSON 분석 결과를 HTML로 변환하는 함수
function generateResultHtml(data) {
    const positiveList = data.positive_summary.map(item => `<li>${item}</li>`).join('');
    const negativeList = data.negative_summary.map(item => `<li>${item}</li>`).join('');

    return `
        <div class="result-header">
            <p><strong>${data.product_name} 리뷰 분석 완료</strong></p>
        </div>

        <div class="result-body">
            <p class="keyword-info">분석 키워드: <strong>${data.keyword}</strong></p>
            
            <div class="section-title summary-score">
                <i class="fa-solid fa-star"></i>
                <span>종합 평점: <strong>${data.rating}</strong></span>
            </div>

            <div class="section-title positive">
                <i class="fa-solid fa-circle-check"></i>
                <span>주요 긍정 요약:</span>
            </div>
            <ul class="summary-list">
                ${positiveList}
            </ul>

            <div class="section-title negative">
                <i class="fa-solid fa-circle-xmark"></i>
                <span>부정적 의견:</span>
            </div>
            <ul class="summary-list">
                ${negativeList}
            </div>

            <div class="save-prompt">
                <p>이 분석 결과를 저장하시겠습니까?</p>
            </div>
        </div>
    `;
}