import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // 1. 화면 상태 관리 ('chat', 'saved', 'settings', 'login', 'signup')
  const [currentView, setCurrentView] = useState('chat');

  // 2. 테마 관리
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 3. 로그인 상태 관리 (Mock)
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  // 4. 저장된 리뷰 데이터 관리
  const [savedItems, setSavedItems] = useState([]);

  // 테마 변경 효과 적용
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
    // 중복 저장 방지 (ID 기준)
    if (!savedItems.some(item => item.id === reviewData.id)) {
      setSavedItems([reviewData, ...savedItems]);
      return true; // 저장 성공
    }
    return false; // 이미 저장됨
  };

  return (
    <AppContext.Provider value={{
      currentView, setCurrentView,
      isDarkMode, setIsDarkMode,
      isLoggedIn, login, logout, user,
      savedItems, saveReview
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);