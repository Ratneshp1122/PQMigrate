import React from 'react';
import clsx from 'clsx';

type BadgeProps = {
  children: React.ReactNode;
  variant?: 'critical' | 'high' | 'medium' | 'safe' | 'abstain' | 'pending';
};

const variants = {
  critical: 'bg-red-500/10 text-red-400 border-red-500/20',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  safe: 'bg-green-500/10 text-green-400 border-green-500/20',
  abstain: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  pending: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
};

export default function Badge({ children, variant = 'pending' }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border',
      variants[variant]
    )}>
      {children}
    </span>
  );
}
