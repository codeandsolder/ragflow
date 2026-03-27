import api from '@/utils/api';
import { useQuery } from '@tanstack/react-query';
import { useFetchCommon } from './common-hooks';

interface LiteLLMStatus {
  status: 'alive' | 'error';
  message: string;
}

export function useFetchLiteLLMStatus() {
  const { isCurrentTenantAdmin } = useFetchCommon();

  const { data, isLoading, refetch } = useQuery<LiteLLMStatus>({
    queryKey: ['litellmStatus'],
    queryFn: async () => {
      const response = await api.get('/api/v1/system/litellm/status');
      return response.data.data;
    },
    enabled: isCurrentTenantAdmin,
    staleTime: 1000 * 60,
    refetchInterval: 1000 * 60 * 5,
  });

  return { data, isLoading, refetch };
}
