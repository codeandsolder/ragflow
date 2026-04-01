import { Authorization } from '@/constants/authorization';
import { cn } from '@/lib/utils';
import FileError from '@/pages/document-viewer/file-error';
import { getAuthorization } from '@/utils/authorization-util';
import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';

interface MdProps {
  // filePath: string;
  className?: string;
  url: string;
}

export const Md: React.FC<MdProps> = ({ url, className }) => {
  const [content, setContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    fetch(url, { headers: { [Authorization]: getAuthorization() } })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch markdown file');
        return res.text();
      })
      .then((text) => {
        const sanitizedContent = DOMPurify.sanitize(text, {
          ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'em', 'strong', 'a', 'img', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'],
          ALLOWED_ATTR: {
            '*': ['class', 'dir'],
            a: ['href', 'title'],
            img: ['src', 'alt', 'title'],
            code: ['class'],
          },
          ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|data):|[^a-z]|[a-z+.][^:]*)$/i,
        });
        setContent(sanitizedContent);
      })
      .catch((err) => setError(err.message));
  }, [url]);

  if (error) return <FileError>{error}</FileError>;

  return (
    <div
      style={{ padding: 4, overflow: 'scroll' }}
      className={cn(className, 'markdown-body h-[calc(100vh - 200px)]')}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default Md;
