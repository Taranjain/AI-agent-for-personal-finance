import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines Tailwind classes with clsx and twMerge
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formats a numeric value into Indian Rupees (INR) with the ₹ symbol.
 * Example: 120000 -> ₹1,20,000
 * Handles negative values: -15000 -> -₹15,000
 */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '₹0';
  }

  const isNegative = amount < 0;
  const absAmount = Math.abs(amount);

  try {
    const formatted = new Intl.NumberFormat('en-IN', {
      maximumFractionDigits: 0,
    }).format(absAmount);

    return isNegative ? `-₹${formatted}` : `₹${formatted}`;
  } catch {
    return isNegative ? `-₹${absAmount}` : `₹${absAmount}`;
  }
}

/**
 * Formats a percentage value.
 * Example: 15.6 -> "15.6%"
 */
export function formatPercent(rate: number | null | undefined, decimals = 1): string {
  if (rate === null || rate === undefined || isNaN(rate)) {
    return '0%';
  }
  return `${rate.toFixed(decimals)}%`;
}

/**
 * Formats a plain number with Indian separators.
 * Example: 50000 -> "50,000"
 */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }
  return new Intl.NumberFormat('en-IN').format(value);
}

/**
 * Returns color tokens for financial health score
 */
export function getHealthScoreStyle(score: number) {
  if (score >= 80) {
    return {
      text: 'text-emerald-700',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      badge: 'bg-emerald-100 text-emerald-800',
      label: 'Excellent',
    };
  }
  if (score >= 65) {
    return {
      text: 'text-blue-700',
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      badge: 'bg-blue-100 text-blue-800',
      label: 'Good',
    };
  }
  if (score >= 50) {
    return {
      text: 'text-amber-700',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      badge: 'bg-amber-100 text-amber-800',
      label: 'Fair',
    };
  }
  return {
    text: 'text-rose-700',
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    badge: 'bg-rose-100 text-rose-800',
    label: 'Needs Attention',
  };
}
