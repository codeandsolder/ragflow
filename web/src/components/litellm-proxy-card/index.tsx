import { CopyToClipboardWithText } from '@/components/file-upload/copy-to-clipboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTranslate } from '@/hooks/common-hooks';
import { useState } from 'react';

interface LiteLLMProxyCardProps {
  enabled?: boolean;
  proxyUrl?: string;
  adminUrl?: string;
}

const LiteLLMProxyCard = ({
  enabled = true,
  proxyUrl = 'http://litellm:4000',
  adminUrl = 'http://localhost:4000/ui',
}: LiteLLMProxyCardProps) => {
  const { t } = useTranslate('setting');
  const [showAdminUrl, setShowAdminUrl] = useState(false);

  return (
    <Card className="mt-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <span className="text-lg">🔗</span>
            LiteLLM Proxy
          </CardTitle>
          <span
            className={`text-xs px-2 py-1 rounded-full ${
              enabled
                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
            }`}
          >
            {enabled ? '● Enabled' : '○ Disabled'}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            Proxy Endpoint
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-sm bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded">
              {proxyUrl}
            </code>
            <CopyToClipboardWithText text={proxyUrl} />
          </div>
        </div>

        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            Admin Dashboard
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-sm bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded">
              {adminUrl}
            </code>
            <CopyToClipboardWithText text={adminUrl} />
          </div>
        </div>

        <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
            Supported Endpoints:
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
              /v1/chat/completions
            </span>
            <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
              /v1/embeddings
            </span>
            <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
              /anthropic/v1/messages
            </span>
            <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
              /v1/models
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LiteLLMProxyCard;
