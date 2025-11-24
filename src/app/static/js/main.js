// main.js

// 현재 대화 시퀀스 상태를 저장하는 변수
let currentStep = 1; 
let inputLink = ''; 

// --- 더미 데이터 (크롤링에서 얻지 못한 값들을 위한 임시 값) ---
const DUMMY_TOTAL_REVIEWS = 244;
const DUMMY_AVG_RATING = 3.6; 

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

/**
 * 사용자 입력 처리 및 대화 시퀀스 진행 함수
 */
async function handleUserInput() {
    const inputField = document.getElementById('text-input');
    const tipText = document.getElementById('tip-text');
    const inputContent = inputField.value.trim();

    if (inputContent === '') return;

    // 사용자 입력 메시지 출력
    addMessage('user', inputContent);
    inputField.value = ''; 

    if (currentStep === 1) {
        inputLink = inputContent;
        addMessage('system', '링크를 확인했습니다. 분석을 원하시는 **주요 키워드**를 입력해 주세요. (예: 배터리, 카메라, 디자인)');
        currentStep = 2;
        tipText.textContent = 'Tip: 키워드(쉼표로 구분)를 입력하고 전송 버튼을 눌러주세요.';
    } else if (currentStep === 2) {
        const keyword = inputContent;
        await startAnalysis(inputLink, keyword);
        currentStep = 3; 
        tipText.textContent = 'Tip: 새로운 분석을 시작하려면 페이지를 새로고침하세요.';
    } else if (currentStep === 3) {
        addMessage('system', `"${inputContent}"에 대한 추가 액션은 현재 구현되지 않았습니다. 페이지를 새로고침하여 새로운 분석을 시작해 주세요.`);
    }
}

/**
 * Flask API 호출 및 분석 과정 실행 함수
 */
async function startAnalysis(link, keyword) {
    const loadingMsg = addMessage('system', `🔍 **분석 시작**: 입력된 링크와 키워드 "${keyword}"를 기반으로 데이터를 수집 및 분석합니다. 잠시만 기다려 주세요...`, true);
    
    try {
        // 이 부분은 실제 Flask API 경로에 맞게 조정해야 합니다.
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ link: link, keyword: keyword })
        });

        if (loadingMsg) loadingMsg.remove(); 

        const data = await response.json();

        if (response.ok) {
            const resultHtml = generateResultHtml(data.result_json);
            addMessage('result', resultHtml);
        } else {
            addMessage('system', `❌ 분석 실패: ${data.message || '알 수 없는 오류가 발생했습니다.'}`);
        }

    } catch (error) {
        if (loadingMsg) loadingMsg.remove();
        addMessage('system', `🚫 네트워크 또는 서버 연결 오류가 발생했습니다: ${error.message}`);
        console.error('Fetch Error:', error);
    }
}

/**
 * 새로운 메시지를 채팅 영역에 추가하는 함수 (타임스탬프 위치 수정)
 */
function addMessage(type, content, isTemporary = false) {
    const chatArea = document.querySelector('.chat-area');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    
    if (type === 'user') {
        messageDiv.classList.add('user-message');
        messageDiv.innerHTML = `<div class="link-bubble">${content}</div>`;
    } else if (type === 'system') {
        messageDiv.classList.add('system-message');
        messageDiv.innerHTML = `<p>${content}</p>`;
    } else if (type === 'result') {
        // 리포트 박스
        messageDiv.classList.add('system-message', 'analysis-result-box');
        messageDiv.innerHTML = content; 
    }

    // 타임스탬프 생성
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? '오후' : '오전';
    const displayHours = hours % 12 || 12; 
    const timeString = `${ampm} ${displayHours}:${minutes}`;
    
    const timestampSpan = `<span class="timestamp">${timeString}</span>`;

    if (type === 'user') {
        // 사용자 메시지: 아래, 오른쪽
        messageDiv.innerHTML += timestampSpan;
    } else if (type === 'system') {
        // 시스템 메시지: 아래, 왼쪽 (CSS에서 .system-message .timestamp로 정렬)
        messageDiv.innerHTML += timestampSpan;
    } else if (type === 'result') {
        // 리포트 메시지: 박스 밖에, 왼쪽 (CSS에서 .system-message .timestamp로 정렬)
        chatArea.appendChild(messageDiv);
        
        // 리포트 박스 바로 아래에 타임스탬프를 추가 (별도의 메시지 DIV로)
        const timestampDiv = document.createElement('div');
        timestampDiv.classList.add('message', 'system-message', 'timestamp-wrapper');
        timestampDiv.style.marginBottom = '25px'; // 다음 메시지와의 간격
        timestampDiv.innerHTML = timestampSpan;
        
        // 리포트의 타임스탬프는 왼쪽 정렬
        timestampDiv.querySelector('.timestamp').style.alignSelf = 'flex-start';
        timestampDiv.querySelector('.timestamp').style.marginLeft = '0';
        timestampDiv.querySelector('.timestamp').style.marginRight = '0';

        chatArea.appendChild(timestampDiv);
        chatArea.scrollTop = chatArea.scrollHeight; 
        return messageDiv; // isTemporary가 true일 경우를 대비하여 반환
    }

    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight; 

    if (isTemporary) {
        return messageDiv;
    }
    return null;
}


/**
 * AI JSON 응답을 기반으로 상세 리포트 HTML을 생성하는 함수 (UI 일치 확인)
 */
function generateResultHtml(data) {
    if (!data || !data.keywords_analysis) {
        return '<p>분석 결과를 불러오지 못했거나 데이터 구조가 올바르지 않습니다.</p>';
    }

    let keywordsCount = data.keywords_analysis.length;
    
    let resultHtml = `
        <div class="result-container">
            <h2 class="section-subtitle">${data.product_name || '제품'} 리뷰 분석 결과</h2>
            
            <section class="overview-section">
                <div class="metrics-grid">
                    <div class="metric-box total-reviews">
                        <h3>${DUMMY_TOTAL_REVIEWS}</h3>
                        <p>총 리뷰 수</p>
                    </div>
                    <div class="metric-box avg-rating">
                        <h3>${DUMMY_AVG_RATING}</h3>
                        <p>평균 평점</p>
                    </div>
                    <div class="metric-box analyzed-keywords">
                        <h3>${keywordsCount}</h3>
                        <p>분석된 키워드</p>
                    </div>
                </div>
                <div class="summary-box">
                    <h4>⭐ 전체 요약</h4>
                    <p>${data.overall_sentiment_summary || '전반적인 감성 요약 내용이 없습니다.'}</p>
                </div>
            </section>
            
            <h3 class="section-subtitle" style="margin-top: 40px;">키워드별 상세 분석</h3>

            <section class="keywords-analysis-section">
                <div class="analysis-list">
    `;

    data.keywords_analysis.forEach(item => {
        const positiveCount = Number(item.positive_count) || 0;
        const negativeCount = Number(item.negative_count) || 0;
        const totalCount = positiveCount + negativeCount;
        
        let positivePercentage = 0;
        let negativePercentage = 0;

        if (totalCount > 0) {
            positivePercentage = (positiveCount / totalCount) * 100;
            negativePercentage = (negativeCount / totalCount) * 100;
        }
        
        resultHtml += `
            <div class="keyword-item">
                <h4>${item.keyword}</h4>
                
                <div class="counts-grid">
                    <div class="count-box positive-bar-group">
                        <div class="count-header">
                            <p class="count-label">긍정 리뷰</p> 
                            <span class="count-number positive">${positiveCount}</span>
                        </div>
                        <div class="bar-wrapper">
                            <div class="count-bar positive" style="width: ${positivePercentage.toFixed(1)}%;"></div>
                        </div>
                        <span class="percentage">${positivePercentage.toFixed(1)}%</span>
                    </div>
                    
                    <div class="count-box negative-bar-group">
                        <div class="count-header">
                            <p class="count-label">부정 리뷰</p>
                            <span class="count-number negative">${negativeCount}</span>
                        </div>
                        <div class="bar-wrapper">
                            <div class="count-bar negative" style="width: ${negativePercentage.toFixed(1)}%;"></div>
                        </div>
                        <span class="percentage">${negativePercentage.toFixed(1)}%</span>
                    </div>
                </div>

                <div class="summary-detail positive-summary-detail">
                    <strong><i class="fa-regular fa-thumbs-up"></i> 긍정 리뷰 요약</strong>
                    <p>${item.positive_summary}</p>
                </div>

                <div class="summary-detail negative-summary-detail" style="margin-top: 15px;">
                    <strong><i class="fa-regular fa-thumbs-down"></i> 부정 리뷰 요약</strong>
                    <p>${item.negative_summary}</p>
                </div>
            </div>
        `;
    });
    
    resultHtml += `
                </div>
            </section>
            
            <div class="save-prompt" style="text-align: center; margin-top: 30px;">
                <p>✅ 분석이 완료되었습니다. 새로운 분석을 시작하려면 링크와 키워드를 다시 입력해주세요.</p>
            </div>
        </div>
    `;

    return resultHtml;
}