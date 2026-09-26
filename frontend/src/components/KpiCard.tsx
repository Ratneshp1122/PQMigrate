import clsx from 'clsx';

type KpiCardProps = {
  title: string;
  value: number | string;
  subtitle?: string;
  borderColor?: 'blue' | 'red' | 'green' | 'purple' | 'orange';
};

const borderColors = {
  blue: 'border-l-blue-500',
  red: 'border-l-red-500',
  green: 'border-l-green-500',
  purple: 'border-l-purple-500',
  orange: 'border-l-orange-500',
};

export default function KpiCard({ title, value, subtitle, borderColor = 'blue' }: KpiCardProps) {
  return (
    <div className={clsx(
      'bg-gray-900 border border-gray-800 rounded-lg p-6 border-l-4 shadow-sm',
      borderColors[borderColor]
    )}>
      <h3 className="text-sm font-medium text-gray-400 mb-1">{title}</h3>
      <div className="text-3xl font-bold text-gray-100">{value}</div>
      {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
    </div>
  );
}
