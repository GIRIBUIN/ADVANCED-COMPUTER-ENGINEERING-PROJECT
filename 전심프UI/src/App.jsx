import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import SavedPage from './pages/SavedPage';
import SettingsPage from './pages/SettingsPage';
import AuthPage from './pages/AuthPage';

const MainContent = () => {
  const { currentView } = useApp();

  if (currentView === 'login' || currentView === 'signup') {
    return (
        <Layout>
            <AuthPage />
        </Layout>
    );
  }

  return (
    <Layout>
      {currentView === 'chat' && <ChatPage />}
      {currentView === 'saved' && <SavedPage />}
      {currentView === 'settings' && <SettingsPage />}
    </Layout>
  );
};

const App = () => {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
};

export default App;