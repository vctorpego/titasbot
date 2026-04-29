import React from 'react';
import Markdown from 'react-markdown';
import { User } from 'lucide-react';
import { cn } from '../lib/utils';
import { motion } from 'motion/react';
import { BotIcon } from './BotIcon';

interface ChatMessageProps {
  role: 'user' | 'ai';
  content: string;
  images?: { url: string; description: string }[];
}

export function ChatMessage({ role, content, images }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'flex w-full py-6 px-4 md:px-6',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-3xl mx-auto flex gap-4 w-full',
          isUser ? 'flex-row-reverse' : 'flex-row'
        )}
      >
        <div className="flex-shrink-0 mt-1">
          {isUser ? (
            <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center shadow-sm border border-gray-300 dark:border-gray-700">
              <User size={16} className="text-gray-600 dark:text-gray-200" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-800 flex items-center justify-center shadow-sm border border-gray-400 dark:border-gray-700">
              <BotIcon size={18} className="text-white" />
            </div>
          )}
        </div>

        <div className={cn('flex-1 space-y-4 overflow-hidden', isUser ? 'flex flex-col items-end' : '')}>
          <div
            className={cn(
              'prose dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-100 dark:prose-pre:bg-[#1a1a1a] prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-gray-800',
              isUser
                ? 'bg-gray-100 dark:bg-[#252525] border border-gray-200 dark:border-gray-700/50 px-5 py-3 rounded-2xl rounded-tr-sm text-left inline-block shadow-sm'
                : 'text-gray-800 dark:text-gray-200'
            )}
          >
            <Markdown>{content}</Markdown>
          </div>

          {images && images.length > 0 && (
            <div
              className={cn(
                'flex gap-4 overflow-x-auto pb-2 pt-2 snap-x max-w-full',
                isUser ? 'justify-end' : 'justify-start'
              )}
            >
              {images.map((img, idx) => (
                <div
                  key={idx}
                  className="flex-shrink-0 w-64 rounded-lg overflow-hidden bg-white dark:bg-[#2d2d2d] shadow-md snap-center border border-gray-200 dark:border-gray-700"
                >
                  <img src={img.url} alt={img.description} className="w-full h-40 object-cover" referrerPolicy="no-referrer" />
                  <div className="p-3">
                    <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 text-left">{img.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
