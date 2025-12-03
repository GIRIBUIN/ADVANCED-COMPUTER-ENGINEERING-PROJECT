// 전역 상태 관리
const STATE = {
    currentScreen: 'main', // 'main', 'currentAnalysis', 'savedReviews', 'login', 'register', 'settings'
    isAuthenticated: false,
    user: { username: null, email: null },
    chatHistory: [], // 현재 분석 화면의 대화 목록 (system/user)
    analysisResult: null, // AI 분석 완료된 결과 데이터
    // localStorage에서 데이터를 로드하고, 없으면 빈 배열로 초기화
    savedData: JSON.parse(localStorage.getItem('savedReviews')) || [], 
    tempUrl: null, // 임시로 저장된 URL
};

// DOM 요소 캐시
const elements = {
    contentContainer: document.getElementById('content-container'),
    authLink: null, // initialize에서 설정됨
    userInfo: null, // initialize에서 설정됨
    currentUsername: null, // initialize에서 설정됨
    modalContainer: null, // initialize에서 설정됨
};

// --- 초기화 ---
function initialize() {
    // DOM 요소 초기화
    elements.authLink = document.getElementById('auth-link');
    elements.userInfo = document.getElementById('user-info');
    elements.currentUsername = document.getElementById('current-username');
    elements.modalContainer = document.getElementById('modal-container');

    // localStorage에서 사용자 상태 로드
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
        STATE.isAuthenticated = true;
        STATE.user.username = JSON.parse(storedUser).username;
    }
    
    // 초기 화면은 '현재 분석 화면'으로
    STATE.currentScreen = 'currentAnalysis';
    updateUI();
}

// --- 헬퍼 함수 ---

// UI 상태 업데이트 및 화면 렌더링
function updateUI() {
    // 1. 네비게이션 메뉴 스타일 업데이트
    document.querySelectorAll('nav a').forEach(a => {
        a.classList.remove('bg-indigo-50', 'text-indigo-700');
        a.classList.add('text-gray-700', 'hover:bg-gray-100');
    });
    const activeScreen = STATE.currentScreen === 'login' || STATE.currentScreen === 'register' ? 'currentAnalysis' : STATE.currentScreen;
    const activeMenu = document.getElementById(`menu-${activeScreen}`);
    if (activeMenu) {
        activeMenu.classList.add('bg-indigo-50', 'text-indigo-700');
        activeMenu.classList.remove('text-gray-700', 'hover:bg-gray-100');
    }

    // 2. 인증 상태 UI 업데이트
    if (STATE.isAuthenticated) {
        elements.authLink.innerHTML = '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3v-1m18-8V9a3 3 0 00-3-3h-2"></path></svg>로그아웃';
        elements.authLink.onclick = handleLogout;
        elements.authLink.classList.add('hidden');
        elements.userInfo.classList.remove('hidden');
        elements.currentUsername.textContent = STATE.user.username;
    } else {
        elements.authLink.innerHTML = '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3v-1m18-8V9a3 3 0 00-3-3h-2"></path></svg>로그인';
        elements.authLink.onclick = () => changeScreen('login');
        elements.authLink.classList.remove('hidden');
        elements.userInfo.classList.add('hidden');
    }

    // 3. 콘텐츠 렌더링
    renderContent();
}

// 화면 전환 함수
function changeScreen(screen) {
    // '새 분석 시작' (main) 클릭 시 채팅 기록 초기화
    if (screen === 'main') {
        STATE.chatHistory = [];
        STATE.analysisResult = null;
        screen = 'currentAnalysis'; // '현재 분석 화면'으로 이동
    }

    // '저장된 리뷰'는 로그인해야 접근 가능
    if (screen === 'savedReviews' && !STATE.isAuthenticated) {
        showModal(getLoginRequiredModal());
        return;
    }

    STATE.currentScreen = screen;
    updateUI();
}

// 채팅 기록 및 화면 업데이트
function pushChat(role, content) {
    STATE.chatHistory.push({ role, content, timestamp: new Date().toLocaleTimeString() });
    renderChatArea();
}

// --- 모달 함수 ---

function showModal(contentHtml) {
    elements.modalContainer.innerHTML = contentHtml;
    elements.modalContainer.classList.remove('hidden');
}

function closeModal() {
    elements.modalContainer.classList.add('hidden');
    elements.modalContainer.innerHTML = '';
}

// --- 로그인/회원가입 처리 (Mock) ---

function handleAuthClick() {
    if (STATE.isAuthenticated) {
        handleLogout();
    } else {
        changeScreen('login');
    }
}

function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;

    const storedUser = localStorage.getItem('user');
    
    if (storedUser) {
        const user = JSON.parse(storedUser);
        if (user.username === username && user.password === password) {
            STATE.isAuthenticated = true;
            STATE.user.username = username;
            closeModal();
            changeScreen('currentAnalysis'); 
            updateUI();
            return;
        }
    }

    // 저장된 계정이 없거나 비밀번호 불일치 시
    // NOTE: alert() 대신 메시지 모달을 사용해야 하지만, 편의상 alert 사용
    alert("아이디 또는 비밀번호가 일치하지 않거나, 등록되지 않은 계정입니다. 회원가입을 먼저 해주세요."); 
}

function handleRegister(e) {
    e.preventDefault();
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;
    
    // Mock 회원가입 로직
    if (localStorage.getItem('user')) {
        alert("Mock 환경에서는 이미 계정이 존재합니다. 로그인 해주세요.");
        return;
    }
    
    if (username && password) {
        const newUser = { username, password };
        localStorage.setItem('user', JSON.stringify(newUser));
        alert("회원가입이 완료되었습니다. 로그인 해주세요.");
        changeScreen('login');
        return;
    }

    alert("아이디와 비밀번호를 모두 입력해야 합니다.");
}

function handleLogout() {
    STATE.isAuthenticated = false;
    STATE.user.username = null;
    updateUI();
    // NOTE: alert() 대신 메시지 모달을 사용해야 하지만, 편의상 alert 사용
    alert("로그아웃되었습니다.");
}

// --- AI 분석 및 크롤링 처리 (Mock) ---

// AI 응답 시뮬레이션 데이터 (app.py의 응답 형식 모방)

// AI 분석 실행 (Mock)
async function runAnalysis(link, keyword) {
    const inputElement = document.getElementById('chat-input');
    const buttonElement = document.querySelector('#input-container button');

    if (!inputElement || !buttonElement) return;

    // 1. 사용자 입력 출력
    pushChat('user', `링크: ${link}, 키워드: ${keyword}`);
    
    // 2. System: 크롤링/분석 시작 메시지
    pushChat('system', '제공된 링크로 접속하여 리뷰를 크롤링하고 AI 분석을 시작합니다. 잠시 기다려주세요...');

    // 입력 비활성화 (로딩 상태)
    inputElement.disabled = true;
    buttonElement.disabled = true;
    buttonElement.innerHTML = '<svg class="animate-spin w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356-2A8.001 8.001 0 004.582 19m9.625-3.5H19V14a5 5 0 10-10 0v1h10"></path></svg>'; // 로딩 아이콘 추가

    try {
        // 서버 통신: app.py의 /api/analyze 호출
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ link, keyword }),
        });
        
        const data = await response.json();

        if (response.ok) {
            // 성공 응답 처리
            STATE.analysisResult = data.result_json;
            pushChat('system', `__ANALYSIS_RESULT_CARD__`); // 마커
            
        } else {
            // 서버 오류 (4xx, 5xx) 응답 처리
            const errorMessage = data.message || "알 수 없는 서버 오류가 발생했습니다.";
            pushChat('system', `🚫 분석 중 오류가 발생했습니다: ${errorMessage}`);
            // 원본 AI 응답이 있다면 추가 정보 제공 (디버깅용)
            if (data.raw_response) {
                console.error("Raw AI Response Error:", data.raw_response);
                pushChat('system', `(디버그 정보: AI 응답 형식이 올바르지 않거나 크롤링에 실패했습니다.)`);
            }
        }
        
    } catch (error) {
        console.error("Network or Fetch Error:", error);
        pushChat('system', `🚫 네트워크 연결 또는 분석 요청 중 오류가 발생했습니다: ${error.message}. 서버(Flask)가 실행 중인지 확인해주세요.`);
    } finally {
        // 입력 활성화 및 버튼 복원
        inputElement.disabled = false;
        buttonElement.disabled = false;
        buttonElement.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>'; // 원래 아이콘 복원
    }
}

// --- 데이터 저장 및 로드 ---

function handleSaveAnalysis() {
    if (!STATE.isAuthenticated) {
        showModal(getLoginRequiredModal());
        return;
    }
    if (!STATE.analysisResult) {
        showModal(getMessageModal('저장 불가', '분석 결과가 없습니다. 먼저 분석을 완료해 주세요.'));
        return;
    }

    const keywordChat = STATE.chatHistory.find(c => c.role === 'user' && c.content.includes('키워드:'));
    // const keyword = keywordChat ? keywordChat.content.split('키워드: ')[1].split(',')[0].trim() : '분석 키워드';
    let keyword = '분석 키워드';
    if (keywordChat) {
        // '키워드: ' 접두사를 제거한 나머지 문자열 전체를 저장
        keyword = keywordChat.content.split('키워드: ')[1].trim(); 
    }

    const newReview = {
        id: Date.now(),
        date: new Date().toLocaleDateString('ko-KR'),
        keyword: keyword,
        result: STATE.analysisResult,
    };

    STATE.savedData.unshift(newReview); // 최신 데이터를 맨 앞에 추가
    localStorage.setItem('savedReviews', JSON.stringify(STATE.savedData));
    showModal(getMessageModal('저장 성공', '현재 분석 결과가 ' + STATE.user.username + '님의 라이브러리에 저장되었습니다.'));

    if (STATE.currentScreen === 'savedReviews') {
        updateUI(); // 저장된 리뷰 화면 강제 업데이트
    }
}

function handleDeleteReview(id) {
    // NOTE: window.confirm() 대신 커스텀 모달을 사용해야 하지만, 편의상 confirm 사용
    if (confirm("정말로 이 저장된 리뷰를 삭제하시겠습니까?")) {
        STATE.savedData = STATE.savedData.filter(item => item.id !== id);
        localStorage.setItem('savedReviews', JSON.stringify(STATE.savedData));
        updateUI();
        showModal(getMessageModal('삭제 완료', '저장된 리뷰가 성공적으로 삭제되었습니다.'));
    }
}

// --- 템플릿 HTML 생성 함수 ---

function getLoginForm() {
    return `
        <div class="bg-white p-8 rounded-xl shadow-2xl w-full max-w-sm">
            <h2 class="text-2xl font-bold mb-6 text-gray-800 text-center">다시 오셨군요!</h2>
            <form onsubmit="handleLogin(event)">
                <div class="mb-4">
                    <label for="login-username" class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                    <input type="text" id="login-username" name="username" value="user123" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="mb-6">
                    <label for="login-password" class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                    <input type="password" id="login-password" name="password" value="password" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white p-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors duration-200">로그인</button>
            </form>
            <div class="mt-4 text-center text-sm">
                계정이 없으신가요? <a href="#" onclick="changeScreen('register')" class="text-indigo-600 font-medium hover:underline">회원가입</a>
            </div>
        </div>
    `;
}

function getRegisterForm() {
    return `
        <div class="bg-white p-8 rounded-xl shadow-2xl w-full max-w-sm">
            <h2 class="text-2xl font-bold mb-6 text-gray-800 text-center">회원가입</h2>
            <form onsubmit="handleRegister(event)">
                <div class="mb-4">
                    <label for="register-username" class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                    <input type="text" id="register-username" name="username" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="mb-6">
                    <label for="register-password" class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                    <input type="password" id="register-password" name="password" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white p-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors duration-200">회원가입</button>
            </form>
            <div class="mt-4 text-center text-sm">
                이미 계정이 있으신가요? <a href="#" onclick="changeScreen('login')" class="text-indigo-600 font-medium hover:underline">로그인</a>
            </div>
        </div>
    `;
}

function getLoginRequiredModal() {
    return `
        <div class="bg-white p-6 rounded-xl shadow-2xl w-full max-w-xs text-center">
            <div class="text-red-500 mb-4">
                <svg class="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            </div>
            <h3 class="text-lg font-bold mb-2">로그인 필수</h3>
            <p class="text-sm text-gray-600 mb-4">저장된 리뷰는 로그인한 사용자만 접근할 수 있습니다.</p>
            <button onclick="closeModal(); changeScreen('login');" class="bg-indigo-600 text-white p-2 rounded-lg font-semibold w-full hover:bg-indigo-700 transition-colors">로그인 하러 가기</button>
        </div>
    `;
}

function getMessageModal(title, message) {
    return `
        <div class="bg-white p-6 rounded-xl shadow-2xl w-full max-w-xs text-center">
            <h3 class="text-lg font-bold mb-2">${title}</h3>
            <p class="text-sm text-gray-600 mb-4">${message}</p>
            <button onclick="closeModal()" class="bg-indigo-600 text-white p-2 rounded-lg font-semibold w-full hover:bg-indigo-700 transition-colors">확인</button>
        </div>
    `;
}

// AI 분석 결과 카드 HTML 
function getAnalysisCard(result) {
    const isCurrentAnalysis = STATE.currentScreen === 'currentAnalysis';
    
    // 1. 전체 리뷰 분석 섹션 HTML 생성
    // keywords_analysis가 없거나 배열이 아니면 0으로 처리 (오류 방지)
    const keywordsAnalysis = Array.isArray(result.keywords_analysis) ? result.keywords_analysis : [];
    const totalPositive = keywordsAnalysis.reduce((sum, k) => sum + k.positive_count, 0);
    const totalNegative = keywordsAnalysis.reduce((sum, k) => sum + k.negative_count, 0);
    const totalReviewCount = totalPositive + totalNegative;
    const neutralCount = Math.round(totalReviewCount * 0.2); // 중립

    
    
    
    const overallAnalysisHtml = `
        <div class="bg-white p-6 rounded-xl shadow-lg w-full max-w-4xl mx-auto mt-4 border border-gray-200">
            <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">📝 감정 분석</h2>
            <div class="flex space-x-4 mb-6 text-center">
                <div class="flex-1 p-4 rounded-lg bg-green-50">
                    <div class="text-2xl font-extrabold text-green-700">${totalPositive}</div>
                    <div class="text-sm font-medium text-green-600">긍정적 리뷰</div>
                </div>
                <div class="flex-1 p-4 rounded-lg bg-yellow-50">
                    <div class="text-2xl font-extrabold text-yellow-700">${neutralCount}</div>
                    <div class="text-sm font-medium text-yellow-600">중립적 리뷰</div>
                </div>
                <div class="flex-1 p-4 rounded-lg bg-red-50">
                    <div class="text-2xl font-extrabold text-red-700">${totalNegative}</div>
                    <div class="text-sm font-medium text-red-600">부정적 리뷰</div>
                </div>
            </div>

            <div class="p-4 bg-indigo-50 rounded-lg">
                <h3 class="text-lg font-semibold text-indigo-800 mb-2">⭐ 전반적 감정 요약</h3>
                <p class="text-sm text-indigo-700">${result.overall_sentiment_summary || '요약 정보가 없습니다.'}</p>
            </div>
        </div>
    `;

    // 2. 키워드별 상세 분석 섹션 HTML 생성
    const keywordsAnalysisHtml = keywordsAnalysis.map(k => {
        const keywordTotal = k.positive_count + k.negative_count;
        const positiveKeywordPercentage = keywordTotal > 0 ? Math.round((k.positive_count / keywordTotal) * 100) : 0;
        const negativeKeywordPercentage = 100 - positiveKeywordPercentage;

        return `
            <div class="mb-8 p-6 bg-white rounded-xl shadow-md border border-gray-100">
                <h3 class="text-xl font-bold text-gray-900 mb-4">#${k.keyword}</h3>
                
                <div class="flex items-center space-x-4 mb-4">
                    <div class="w-1/3 text-right text-sm font-semibold text-green-700">${k.positive_count}</div>
                    <div class="flex-1 h-3 rounded-full overflow-hidden bg-red-100">
                        <div class="bg-green-500 h-3" style="width: ${positiveKeywordPercentage}%;"></div>
                    </div>
                    <div class="w-1/3 text-left text-sm font-semibold text-red-700">${k.negative_count}</div>
                </div>
                
                <div class="flex justify-between text-xs font-medium text-gray-600 mb-6">
                    <span>긍정 (${positiveKeywordPercentage}%)</span>
                    <span>부정 (${negativeKeywordPercentage}%)</span>
                </div>

                <div class="bg-green-50 p-4 rounded-lg mb-4 border border-green-200">
                    <div class="flex items-center text-green-700 font-bold mb-2">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        긍정 리뷰 요약
                    </div>
                    <p class="text-sm text-green-800">${k.positive_summary}</p>
                </div>
                
                <div class="bg-red-50 p-4 rounded-lg border border-red-200">
                    <div class="flex items-center text-red-700 font-bold mb-2">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        부정 리뷰 요약
                    </div>
                    <p class="text-sm text-red-800">${k.negative_summary}</p>
                </div>
            </div>
        `;
    }).join('');

    // 3. 전체 레이아웃 구성
    return `
        <div class="flex flex-col w-full max-w-4xl mx-auto">
            <div class="text-center mb-6">
                <h1 class="text-2xl font-extrabold text-gray-800">${result.product_name || '제품명 없음'} 분석 결과</h1>
            </div>

            ${overallAnalysisHtml}
            
            <div class="mt-8">
                <h2 class="text-xl font-bold text-gray-900 mb-4 pb-2 border-b">🔍 키워드별 상세 분석</h2>
                ${keywordsAnalysisHtml}
            </div>

            ${isCurrentAnalysis ? 
                `<div class="mt-8 pt-6 border-t text-center sticky bottom-0 bg-white p-4 shadow-xl rounded-lg">
                    <button onclick="handleSaveAnalysis()" class="flex items-center justify-center w-full max-w-md mx-auto bg-indigo-600 text-white p-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors duration-200 shadow-md">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4L12 7l-4 4m0 0l4 4m-4-4h8"></path></svg>
                        결과 저장하기
                    </button>
                </div>` 
                : ''}
        </div>
    `;
}

// --- 화면별 렌더링 함수 ---

// 채팅 영역 렌더링
function renderChatArea() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;

    const html = STATE.chatHistory.map(chat => {
        if (chat.role === 'system') {
            // 해당 채팅이 분석 완료 후의 메시지인지 확인하는 방식으로 변경 (혹은 간단하게 포함 여부 유지)
            let contentHtml = '';
            if (chat.content === '__ANALYSIS_RESULT_CARD__') {
                // 분석 결과가 있을 때만 카드 렌더링 (안전을 위한 추가 확인)
                contentHtml = STATE.analysisResult ? getAnalysisCard(STATE.analysisResult) : '<p>분석 결과를 불러오는 데 실패했습니다.</p>';
            } else if (chat.content.includes('🚫')) {
                // 오류 메시지
                contentHtml = `<p class="text-red-600 font-medium">${chat.content}</p>`;
            } else {
                // 일반 시스템 메시지 (크롤링 시작, 키워드 요청 등)
                contentHtml = `<p>${chat.content}</p>`;
            }
            // const contentHtml = STATE.analysisResult && !chat.content.includes('🚫') ? // 오류 메시지가 아닐 경우에만 카드 렌더링
            //     getAnalysisCard(STATE.analysisResult) : 
            //     `<p>${chat.content}</p>`;

            return `
                <div class="flex items-start mb-6">
                    <div class="flex-shrink-0 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-white text-sm mr-4">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 10v2m14-2v2M5 10h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2v-3"></path></svg>
                    </div>
                    <div class="max-w-3xl">
                        <div class="bg-white p-4 rounded-xl shadow-md border border-gray-100">
                            ${contentHtml}
                        </div>
                    </div>
                </div>
            `;
        }
        // User 메시지
        const contentDisplay = chat.content.includes('키워드:') ? 
            `<div class="flex flex-wrap gap-2">${chat.content.split('키워드: ')[1].split(',').map(k => `<span class="px-3 py-1 bg-indigo-700 rounded-full text-xs font-medium">${k.trim()}</span>`).join('')}</div>` : 
            `<p>${chat.content}</p>`;

        return `
            <div class="flex justify-end mb-6">
                <div class="max-w-xl">
                    <div class="bg-indigo-600 text-white p-4 rounded-xl shadow-md">
                        ${contentDisplay}
                    </div>
                </div>
                <div class="flex-shrink-0 w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-gray-700 text-sm ml-4">U</div>
            </div>
        `;
    }).join('');

    chatArea.innerHTML = html;
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 채팅 제출 핸들러
async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const value = input.value.trim();
    input.value = '';

    if (!value) return;

    // 1. URL 입력 단계
    if (STATE.chatHistory.length === 0) {
        const urlRegex = /^(https?:\/\/[^\s]+)$/i;
        if (!urlRegex.test(value)) {
            pushChat('system', '유효한 쇼핑몰 링크(URL)를 입력해주세요.');
            return;
        }
        
        STATE.tempUrl = value;
        pushChat('user', `${value}`);
        pushChat('system', `URL을 확인했습니다. 어떤 키워드로 분석을 진행할까요? (예: 키워드: 배터리, 카메라)`);
    
    // 2. 키워드 입력 단계
    } else if (STATE.chatHistory.length > 0 && STATE.tempUrl) {
        let keywordValue = value;
        if (value.toLowerCase().startsWith('키워드:')) {
            keywordValue = value.substring('키워드:'.length).trim();
        }
        
        if (!keywordValue) {
            pushChat('system', '분석할 키워드를 쉼표로 구분하여 입력해주세요.');
            return;
        }
        
        await runAnalysis(STATE.tempUrl, keywordValue);
        delete STATE.tempUrl;
    
    // 3. 분석 완료 후
    } else {
         pushChat('system', '새로운 분석을 시작하려면 왼쪽 사이드바의 "새 분석 시작"을 클릭해주세요.');
    }
}

// 현재 분석 화면 렌더링
function renderCurrentAnalysis() {
    elements.contentContainer.innerHTML = `
        <div class="flex flex-col h-[calc(100vh-64px)]">
            <div id="chat-area" class="flex-1 overflow-y-auto p-4 hide-scrollbar pt-0">
                ${STATE.chatHistory.length === 0 ? `
                    <div class="flex items-start mb-6 pt-8">
                        <div class="flex-shrink-0 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-white text-sm mr-4">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 10v2m14-2v2M5 10h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2v-3"></path></svg>
                        </div>
                        <div class="max-w-3xl">
                            <div class="bg-white p-4 rounded-xl shadow-md border border-gray-100">
                                <p>안녕하세요! 쇼핑몰 링크(URL)를 입력하시면 리뷰 분석을 시작할 수 있습니다.</p>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>

            <div id="input-container" class="sticky bottom-0 bg-white p-4 border-t border-gray-200">
                <form id="chat-form" class="flex" onsubmit="handleChatSubmit(event)">
                    <input type="text" id="chat-input" placeholder="쇼핑몰 링크 또는 키워드를 입력하세요..." required
                        class="flex-1 p-4 border border-gray-300 rounded-l-xl focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-shadow shadow-inner">
                    <button type="submit" class="bg-indigo-600 text-white p-4 rounded-r-xl font-semibold hover:bg-indigo-700 transition-colors duration-200 flex items-center justify-center">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                    </button>
                </form>
                <p class="text-xs text-gray-500 mt-2 text-center">
                    예시: https://example.com/product/123 또는 키워드: 배터리, 카메라
                </p>
            </div>
        </div>
    `;
    // 채팅 기록이 있다면 다시 렌더링
    if (STATE.chatHistory.length > 0) {
        renderChatArea();
    }
}

// 저장된 리뷰 화면 렌더링
function renderSavedReviews() {
    if (!STATE.isAuthenticated) return;

    const savedReviewsHtml = STATE.savedData.length > 0 ? 
        STATE.savedData.map(item => {
            // 키워드 문자열을 쉼표와 공백으로 분리하여 태그로 변환
            const keywordTags = item.keyword
                .split(',')
                .map(k => k.trim())
                .filter(k => k.length > 0)
                .map(k => `<span class="inline-block bg-indigo-100 text-indigo-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-full">${k}</span>`)
                .join('');

            return `
            <div class="bg-white p-6 rounded-xl shadow-lg border border-gray-200 mb-6 relative">
                <div class="flex justify-between items-center mb-4 pb-4 border-b">
                    <h3 class="text-lg font-bold text-gray-900">${item.result.product_name || '제품명 없음'}</h3>
                    <div class="text-sm text-gray-500">${item.date}</div>
                </div>
                
                <div class="text-sm font-medium text-gray-600 mb-4 flex items-center">
                    <span class="mr-2">분석 키워드:</span>
                    <div class="flex flex-wrap">${keywordTags}</div>
                </div>
                <div class="flex justify-end space-x-2 border-t pt-4">
                    <button onclick="viewSavedReviewDetails(${item.id})" class="px-3 py-1 bg-indigo-50 border border-indigo-200 text-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-100 transition-colors">
                        상세 보기
                    </button>
                    <button onclick="handleDeleteReview(${item.id})" class="px-3 py-1 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors">
                        삭제
                    </button>
                </div>
            </div>
            `;
        }).join('')
        : '<div class="text-center py-12 text-gray-500">아직 저장된 리뷰가 없습니다. 분석 결과를 저장해보세요!</div>';

    elements.contentContainer.innerHTML = `
        <h1 class="text-2xl font-bold text-gray-900 mb-6">내 라이브러리</h1>
        <div class="max-w-3xl mx-auto">
            ${savedReviewsHtml}
        </div>
    `;
}

// 저장된 리뷰 상세 보기
function viewSavedReviewDetails(id) {
    const review = STATE.savedData.find(item => item.id === id);
    if (review) {
        // 임시로 STATE.currentScreen을 변경하여 저장 버튼이 없는 카드를 렌더링
        const originalScreen = STATE.currentScreen;
        STATE.currentScreen = 'savedReviewsDetail'; 

        const cardHtml = getAnalysisCard(review.result)
            .replace('w-full max-w-xl mx-auto mt-4 border border-gray-200', 'w-full max-w-xl');
        
        showModal(`
            <div class="bg-white p-6 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4 border-b pb-3">
                    <h2 class="text-xl font-bold">저장된 분석 상세</h2>
                    <button onclick="closeModal(); STATE.currentScreen = '${originalScreen}';" class="text-gray-500 hover:text-gray-800 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                ${cardHtml}
                <div class="mt-4 text-center">
                     <button onclick="closeModal(); STATE.currentScreen = '${originalScreen}';" class="mt-4 px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors">닫기</button>
                </div>
            </div>
        `);
        // 모달을 닫을 때 원래 화면으로 돌아가도록 STATE.currentScreen을 복원.
        // 이는 모달의 닫기 버튼/배경 클릭 이벤트에 포함.
    }
}

// 설정 화면 렌더링
function renderSettings() {
    elements.contentContainer.innerHTML = `
        <h1 class="text-2xl font-bold text-gray-900 mb-6">설정</h1>
        <div class="bg-white p-8 rounded-xl shadow-lg max-w-2xl">
            <p class="text-lg font-semibold mb-4">계정 정보</p>
            <div class="space-y-3">
                <div class="flex justify-between border-b pb-2">
                    <span class="text-gray-600">아이디:</span>
                    <span class="font-medium text-gray-900">${STATE.user.username || '비로그인'}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-gray-600">구독 플랜:</span>
                    <span class="font-medium text-green-600">Free Plan</span>
                </div>
            </div>
            
            <button onclick="showModal(getMessageModal('기능 제한', 'Mock 환경이므로 기능이 제한됩니다. 실제 구현에서는 비밀번호 변경 로직을 추가해야 합니다.'))" class="mt-6 px-4 py-2 bg-gray-100 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors">
                비밀번호 변경 (Mock)
            </button>
        </div>
    `;
}

// 메인 렌더링 함수
function renderContent() {
    // 로그인, 회원가입 화면은 메인 콘텐츠 영역에 풀 사이즈로 표시
    elements.modalContainer.classList.add('hidden');
    elements.modalContainer.innerHTML = '';
    
    switch (STATE.currentScreen) {
        case 'login':
            elements.contentContainer.innerHTML = `<div class="flex items-center justify-center min-h-[calc(100vh-32px)]">${getLoginForm()}</div>`;
            break;
        case 'register':
            elements.contentContainer.innerHTML = `<div class="flex items-center justify-center min-h-[calc(100vh-32px)]">${getRegisterForm()}</div>`;
            break;
        case 'savedReviews':
            renderSavedReviews();
            break;
        case 'settings':
            renderSettings();
            break;
        case 'main':
        case 'currentAnalysis':
        default:
            renderCurrentAnalysis();
            break;
    }
}