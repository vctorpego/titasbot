/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, Plus, MessageSquare, ArrowDown, Sun, Moon } from 'lucide-react';
import { ChatMessage } from './components/ChatMessage';
import { BotIcon } from './components/BotIcon';
import { resetBackendSession, sendMessageToBackend } from './services/api';
import { motion, AnimatePresence } from 'motion/react';
import TextareaAutosize from 'react-textarea-autosize';

type Message = {
  id: string;
  role: 'user' | 'ai';
  content: string;
  images?: { url: string; description: string }[];
};

const SUGGESTIONS = [
  'O que são os Titãs da Robótica?',
  'Quais projetos vocês já fizeram?',
  'Como participar da equipe?',
  'Quais tecnologias utilizam?',
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return (
        localStorage.getItem('theme') === 'dark' ||
        (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
      );
    }
    return true;
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isNearBottom && messages.length > 0);
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput('');
    resetBackendSession();
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessageToBackend(text);

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: response.text,
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error('Error querying RAG:', error);
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'ai',
          content:
            error instanceof Error
              ? error.message
              : 'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-[#0f0f0f] text-gray-900 dark:text-gray-100 font-sans relative overflow-hidden transition-colors duration-200">
      <div
        className="absolute inset-0 z-0 opacity-[0.03] dark:opacity-[0.03] pointer-events-none"
        style={{ backgroundImage: 'radial-gradient(currentColor 1px, transparent 1px)', backgroundSize: '24px 24px' }}
      ></div>

      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800/60 bg-white/80 dark:bg-[#0f0f0f]/80 backdrop-blur-md z-20 sticky top-0 transition-colors duration-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gray-300 dark:bg-gray-800 border border-gray-400 dark:border-gray-700 flex items-center justify-center">
            <BotIcon className="text-gray-900 dark:text-gray-100" size={20} />
          </div>
          <h1 className="text-lg font-semibold tracking-tight">TitãsBot</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white bg-gray-100 hover:bg-gray-200 dark:bg-gray-800/50 dark:hover:bg-gray-700/50 rounded-lg transition-colors border border-gray-200 dark:border-gray-700/50"
            title="Alternar tema"
          >
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white bg-gray-100 hover:bg-gray-200 dark:bg-gray-800/50 dark:hover:bg-gray-700/50 rounded-lg transition-colors border border-gray-200 dark:border-gray-700/50"
            title="Novo Chat"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">Novo Chat</span>
          </button>
        </div>
      </header>

      <main ref={scrollContainerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto w-full z-10 scroll-smooth">
        {messages.length === 0 ? (
          <div className="min-h-full flex flex-col items-center justify-center px-4 max-w-3xl mx-auto py-8">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="w-20 h-20 bg-white dark:bg-gray-800/40 rounded-2xl flex items-center justify-center mb-6 border border-gray-300 dark:border-gray-600 shadow-sm backdrop-blur-sm"
            >
              <BotIcon size={40} className="text-gray-900 dark:text-gray-100" />
            </motion.div>
            <h2 className="text-2xl md:text-3xl font-semibold mb-3 text-center text-gray-900 dark:text-gray-100">Como posso ajudar?</h2>
            <div className="text-gray-500 dark:text-gray-400 text-center mb-10 max-w-md text-sm leading-relaxed">
              <p>Olá, eu sou o TitãsBot, o assistente virtual da equipe Titãs da Robótica do Ifes – Campus Colatina.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
              {SUGGESTIONS.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(suggestion)}
                  className="px-4 py-3.5 rounded-xl border border-gray-200 dark:border-gray-800/80 bg-white dark:bg-[#141414] hover:bg-gray-50 dark:hover:bg-[#1e1e1e] hover:border-gray-300 dark:hover:border-gray-700 transition-all text-left flex items-center gap-3 group shadow-sm"
                >
                  <MessageSquare
                    size={16}
                    className="text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors flex-shrink-0"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300 font-medium group-hover:text-gray-900 dark:group-hover:text-gray-100 transition-colors">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="pb-8">
            {messages.map(msg => (
              <ChatMessage key={msg.id} {...msg} />
            ))}
            {isLoading && (
              <div className="flex w-full py-6 px-4 md:px-6">
                <div className="max-w-3xl mx-auto flex gap-4 w-full">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-800 flex items-center justify-center shadow-sm border border-gray-400 dark:border-gray-700">
                      <BotIcon size={18} className="text-white" />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 h-8">
                    <Sparkles size={16} className="animate-pulse text-gray-500 dark:text-gray-300" />
                    <span className="text-sm font-medium animate-pulse">Consultando a base de conhecimento...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </main>

      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            onClick={scrollToBottom}
            className="absolute bottom-32 right-1/2 translate-x-1/2 md:translate-x-0 md:right-8 p-2 bg-white/90 dark:bg-gray-800/90 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-white rounded-full shadow-lg border border-gray-200 dark:border-gray-700 z-30 backdrop-blur-sm transition-colors"
          >
            <ArrowDown size={20} />
          </motion.button>
        )}
      </AnimatePresence>

      <div className="flex-none bg-gradient-to-t from-gray-50 via-gray-50 dark:from-[#0f0f0f] dark:via-[#0f0f0f] to-transparent pt-2 pb-6 px-4 z-20 transition-colors duration-200">
        <div className="max-w-3xl mx-auto relative">
          <form
            onSubmit={e => {
              e.preventDefault();
              handleSend(input);
            }}
            className="relative flex items-end bg-white dark:bg-[#1a1a1a] border border-gray-300 dark:border-gray-700/80 rounded-2xl shadow-lg focus-within:border-gray-500/50 focus-within:ring-1 focus-within:ring-gray-500/50 transition-all overflow-hidden"
          >
            <TextareaAutosize
              minRows={1}
              maxRows={6}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pergunte sobre os Titãs da Robótica..."
              disabled={isLoading}
              className="w-full bg-transparent py-4 pl-5 pr-14 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none resize-none disabled:opacity-50 text-base"
            />
            <div className="absolute right-2 bottom-2">
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-2 bg-gray-300 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:bg-gray-100 disabled:text-gray-400 dark:disabled:bg-gray-800 dark:disabled:text-gray-600 text-gray-700 dark:text-white rounded-xl transition-all flex items-center justify-center h-10 w-10"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} className="ml-0.5" />}
              </button>
            </div>
          </form>
          <div className="text-center mt-3">
            <span className="text-[11px] text-gray-500 font-medium">© Ifes – Campus Colatina. Todos os direitos reservados.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
