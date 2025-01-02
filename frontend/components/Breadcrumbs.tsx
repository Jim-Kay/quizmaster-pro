'use client'

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { getTopic } from '@/lib/api/topics';

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  // Check if we're in a topic route and get the topic ID
  const topicId = segments[1] && segments[0] === 'topics' ? segments[1] : null;
  
  // Fetch topic data if we're in a topic route
  const { data: topic } = useQuery({
    queryKey: ['topic', topicId],
    queryFn: () => getTopic(topicId!),
    enabled: !!topicId,
  });

  // Build breadcrumb items with accumulated paths
  const breadcrumbs = segments.map((segment, index) => {
    const path = `/${segments.slice(0, index + 1).join('/')}`;
    
    // If this segment is a topic ID and we have topic data, use the title instead
    if (segment === topicId && topic) {
      return { name: topic.title, path };
    }
    
    return { name: segment, path };
  });

  return (
    <nav className="flex px-4 py-2 space-x-2 text-sm text-gray-600 border-b border-gray-200">
      <Link 
        href="/"
        className="flex items-center hover:text-gray-900"
      >
        <HomeIcon className="w-4 h-4" />
      </Link>
      
      {breadcrumbs.map((breadcrumb, index) => (
        <div key={breadcrumb.path} className="flex items-center">
          <ChevronRightIcon className="w-4 h-4 mx-1 text-gray-400" />
          <Link
            href={breadcrumb.path}
            className={`hover:text-gray-900 ${
              index === breadcrumbs.length - 1 ? 'text-gray-900 font-medium' : ''
            }`}
          >
            {breadcrumb.name
              .replace(/^\[|\]$/g, '') // Remove square brackets from dynamic segments
              .split('-')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ')}
          </Link>
        </div>
      ))}
    </nav>
  );
}
