import { Breadcrumbs } from '@/components/Breadcrumbs';
import { TopicsSidebar } from '@/components/topics/TopicsSidebar';

export default function TopicsLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <div className="flex flex-col h-full">
      <Breadcrumbs />
      <div className="flex flex-1 overflow-hidden">
        <div className="w-64 border-r border-gray-200 overflow-y-auto">
          <TopicsSidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
      {modal}
    </div>
  );
}
