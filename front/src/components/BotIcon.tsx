import React, { useState } from 'react';

interface BotIconProps {
  className?: string;
  size?: number;
}

export function BotIcon({ className, size = 24 }: BotIconProps) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <span
        style={{ width: size, height: size, fontSize: Math.max(10, Math.round(size * 0.42)) }}
        className={`inline-flex items-center justify-center rounded-full bg-gray-700 text-white font-semibold ${className || ''}`}
      >
        TB
      </span>
    );
  }

  return (
    <img
      src="/logo.png"
      alt="TitãsBot"
      style={{ width: size, height: size }}
      className={`object-contain brightness-0 dark:brightness-100 ${className || ''}`}
      onError={() => setError(true)}
    />
  );
}
