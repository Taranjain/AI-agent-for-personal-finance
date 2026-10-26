import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, HelpCircle } from 'lucide-react';
import { aiApi } from '../lib/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export const ChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your FinWise AI Assistant. Ask me anything about financial concepts, compound interest, SIP strategies, or debt payoff methods!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const quickPrompts = [
    'What is compound interest?',
    'Explain SIP vs Lump Sum',
    'Avalanche vs Snowball method',
  ];

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await aiApi.chat({
        message: textToSend.trim(),
        session_id: sessionId,
      });

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      console.warn('Chat API error, providing local educational response:', err);

      // Educational offline fallback generator for demo continuity
      let fallbackText = 'I am your FinWise educational co-pilot.';
      const lower = textToSend.toLowerCase();

      if (lower.includes('compound interest')) {
        fallbackText =
          'Compound interest is interest calculated on the initial principal and also on the accumulated interest of previous periods. As Einstein famously noted, it is the eighth wonder of the world: those who understand it, earn it; those who don’t, pay it. The formula is A = P(1 + r/n)^(nt).';
      } else if (lower.includes('sip') || lower.includes('lump sum')) {
        fallbackText =
          'A Systematic Investment Plan (SIP) allows you to invest fixed amounts regularly (e.g., monthly). This leverages Rupee Cost Averaging, buying more units when prices drop and fewer when prices rise, eliminating the risk of timing the market. Lump sum works well when you have a large cash surplus and markets are at fair valuations.';
      } else if (lower.includes('avalanche') || lower.includes('snowball')) {
        fallbackText =
          'The Debt Avalanche focuses on paying off debts with the highest interest rate first, minimizing the total interest paid over time (mathematically optimal). The Debt Snowball focuses on clearing the smallest balance first for quick psychological momentum.';
      } else {
        fallbackText =
          'Thank you for your question! In personal finance, maintaining a 6-month emergency reserve and allocating investments across diversified index funds provide the highest risk-adjusted stability.';
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: fallbackText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-[400px] overflow-hidden">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-800">Financial Education Chat</h3>
            <p className="text-[10px] text-slate-400">Ask financial terms & concepts</p>
          </div>
        </div>
        <HelpCircle className="w-4 h-4 text-slate-400" />
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3 bg-slate-50/30">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-2 ${
              msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
            </div>

            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed shadow-xs ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
              }`}
            >
              <p>{msg.text}</p>
              <span
                className={`text-[9px] block text-right mt-1 ${
                  msg.sender === 'user' ? 'text-blue-100' : 'text-slate-400'
                }`}
              >
                {msg.timestamp}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-1">
            <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">
              <Bot className="w-3 h-3 text-slate-400 animate-pulse" />
            </div>
            <div className="flex items-center space-x-1 bg-white border border-slate-200 px-3 py-1.5 rounded-lg">
              <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
              <span className="text-[11px] text-slate-500">AI is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Chips */}
      <div className="px-3 pt-2 pb-1 bg-white border-t border-slate-100 flex flex-wrap gap-1.5">
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSendMessage(prompt)}
            className="text-[10px] bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-600 px-2 py-0.5 rounded-full transition-colors truncate max-w-full"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="p-2.5 bg-white border-t border-slate-100">
        <div className="flex items-center space-x-1.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a financial question..."
            disabled={isLoading}
            className="flex-1 text-xs px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => handleSendMessage()}
            disabled={isLoading || !input.trim()}
            className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
