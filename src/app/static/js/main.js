// main.js

// 현재 대화 시퀀스 상태를 저장하는 변수
let currentStep = 1; // 1: 링크 입력 요구, 2: 키워드 입력 요구, 3: 분석 완료
let inputLink = ''; // 사용자가 입력한 링크 저장

document.addEventListener('DOMContentLoaded', () => {
    // 1. 프로그램 시작 및 시스템 메시지 출력 (링크 입력 요구)
    addMessage('system', '안녕하세요! 제품 리뷰 분석기입니다. 분석하고 싶은 제품의 링크를 입력해 주세요.');

    const sendButton = document.getElementById('send-button');
    const inputField = document.getElementById('text-input');
    
    sendButton.addEventListener('click', handleUserInput);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleUserInput();
        }
    });
});

// 사용자 입력 처리 및 시퀀스 진행 함수
async function handleUserInput() {
    const inputField = document.getElementById('text-input');
    const tipText = document.getElementById('tip-text');
    const inputContent = inputField.value.trim();

    if (inputContent === '') return;

    // 사용자 입력 메시지 출력
    addMessage('user', inputContent);
    inputField.value = ''; // 입력창 초기화

    // 시퀀스 분기 처리
    if (currentStep === 1) {
        // 3. 사용자 링크 입력 완료
        inputLink = inputContent;
        
        // 4. 시스템 메시지 (키워드 입력 요구) 출력
        addMessage('system', '링크를 확인했습니다. 분석을 원하시는 **주요 키워드**를 입력해 주세요. (예: 배터리, 카메라, 디자인)');
        currentStep = 2;
        tipText.textContent = 'Tip: 키워드를 입력하고 전송 버튼을 눌러주세요.';

    } else if (currentStep === 2) {
        // 4. 사용자 키워드 입력 완료
        const keyword = inputContent;
        
        // 5, 6, 7. 크롤링, 전처리, AI 분석 및 결과 출력
        // 사용자가 입력한 링크(inputLink)와 키워드(keyword)를 서버에 전송합니다.
        await startAnalysis(inputLink, keyword);

        // 시퀀스 3으로 이동 (분석 완료 상태)
        currentStep = 3; 
        tipText.textContent = 'Tip: 새로운 분석을 시작하거나 결과 저장 옵션을 선택하세요.';
    
    } else if (currentStep === 3) {
        // 분석 완료 후 추가 대화 로직
        addMessage('system', `"${inputContent}"에 대한 추가 액션(예: 저장)은 현재 구현되지 않았습니다. 페이지를 새로고침하여 새로운 분석을 시작해 주세요.`);
    }
}

// Flask API 호출 및 분석 과정 실행 함수
async function startAnalysis(link, keyword) {
    
    // 로딩 메시지 출력
    const loadingMsg = addMessage('system', `🔍 **분석 시작**: 입력된 링크와 키워드 "${keyword}"를 기반으로 데이터를 수집 및 분석합니다. 잠시만 기다려 주세요...`);
    
    try {
        // Flask 서버의 /api/analyze 엔드포인트에 POST 요청을 보냅니다.
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // link와 keyword를 JSON 바디에 담아 전송
            body: JSON.stringify({ link: link, keyword: keyword })
        });

        // 로딩 메시지 제거
        if (loadingMsg) loadingMsg.remove(); 

        if (response.ok) {
            const data = await response.json();
            
            // 8. 시스템 메시지 출력 (JSON 데이터를 이용한 친화적인 폼)
            const analysisResult = parseAIResponse(data.result_json, data.keyword);
            const resultHtml = generateResultHtml(analysisResult);
            addMessage('result', resultHtml);

        } else {
            const errorData = await response.json();
            addMessage('system', `❌ 분석 실패: ${errorData.message}`);
        }

    } catch (error) {
        if (loadingMsg) loadingMsg.remove();
        addMessage('system', `🚫 네트워크 또는 서버 연결 오류가 발생했습니다: ${error.message}`);
        console.error('Fetch Error:', error);
    }
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
    // 24시간 형식으로 17:08을 '오후 5:08' 형태로 변환 (간단화)
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? '오후' : '오전';
    const displayHours = hours % 12 || 12; // 0시를 12시로 표시
    const timeString = `${ampm} ${displayHours}:${minutes}`;
    messageDiv.innerHTML += `<span class="timestamp">${timeString}</span>`;

    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight; 

    if (isTemporary) {
        return messageDiv; // 임시 메시지일 경우 DOM 요소를 반환하여 나중에 제거할 수 있도록 함
    }
    return null;
}

// AI JSON 응답 파싱 및 형식 변환 (프론트엔드에서 처리)
function parseAIResponse(jsonObj, keyword) {
    // 평점은 크롤링에서 얻어야 하지만, 현재는 임시값 사용
    const result = {
        product_name: "제품 리뷰 분석 완료", 
        keyword: keyword,
        rating: "4.3/5.0", 
        positive_summary: [],
        negative_summary: []
    };

    // JSON 객체를 순회하며 리스트 형태로 변환
    if (jsonObj["긍정적"]) {
        for (const [key, value] of Object.entries(jsonObj["긍정적"])) {
            result.positive_summary.push(`**${key}**: ${value}`);
        }
    }
    if (jsonObj["부정적"]) {
        for (const [key, value] of Object.entries(jsonObj["부정적"])) {
            result.negative_summary.push(`**${key}**: ${value}`);
        }
    }
    
    return result;
}

// 분석 결과를 HTML로 변환하는 함수
function generateResultHtml(data) {
    const positiveList = data.positive_summary.map(item => `<li>${item}</li>`).join('');
    const negativeList = data.negative_summary.map(item => `<li>${item}</li>`).join('');

    return `
        <div class="result-header">
            <p><strong>${data.product_name}</strong></p>
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
                ${positiveList || '<li>긍정적인 내용이 부족하거나 해당 키워드에 대한 언급이 없습니다.</li>'}
            </ul>

            <div class="section-title negative">
                <i class="fa-solid fa-circle-xmark"></i>
                <span>부정적 의견:</span>
            </div>
            <ul class="summary-list">
                ${negativeList || '<li>부정적인 내용이 부족하거나 해당 키워드에 대한 언급이 없습니다.</li>'}
            </ul>

            <div class="save-prompt">
                <p>이 분석 결과를 저장하시겠습니까?</p>
            </div>
        </div>
    `;
}