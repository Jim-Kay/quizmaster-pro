interface PageHeaderProps {
  title: string;
  description?: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="pb-5 border-b border-gray-200">
      <h3 className="text-2xl leading-6 font-medium text-gray-900">{title}</h3>
      {description && (
        <p className="mt-2 max-w-4xl text-sm text-gray-500">{description}</p>
      )}
    </div>
  );
}
