import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // 1. 화면 상태 관리
  const [currentView, setCurrentView] = useState('chat');

  // 2. 테마 관리
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 3. 로그인 상태 관리 (Mock)
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  // 4. 저장된 리뷰 데이터 관리
  const [savedItems, setSavedItems] = useState([]);

  // ★ 5. 채팅 세션 상태 관리 (여기로 이사옴!) ★
  const [chatSession, setChatSession] = useState({
    messages: [],
    stage: 'init', // init, url_received, done 등
    isLoading: false
  });

  // 채팅 초기화 함수 (새 분석 시작용)
  const resetChat = () => {
    setChatSession({
      messages: [],
      stage: 'init',
      isLoading: false
    });
  };

  // 테마 변경 효과
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const login = (username) => {
    setIsLoggedIn(true);
    setUser({ name: username });
    setCurrentView('chat');
  };

  const logout = () => {
    setIsLoggedIn(false);
    setUser(null);
    setCurrentView('login');
  };

  const saveReview = (reviewData) => {
    if (!savedItems.some(item => item.id === reviewData.id)) {
      setSavedItems([reviewData, ...savedItems]);
      return true;
    }
    return false;
  };

  return (
    <AppContext.Provider value={{
      currentView, setCurrentView,
      isDarkMode, setIsDarkMode,
      isLoggedIn, login, logout, user,
      savedItems, saveReview,
      chatSession, setChatSession, resetChat // ★ 추가된 부분
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);