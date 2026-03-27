import { useCallback, useEffect, useState } from 'react';

export function useHandleClickConversationCard() {
  const [controller, setController] = useState(new AbortController());
  const { setConversationBoth } = useChatUrlParams();

  useEffect(() => {
    return () => {
      controller.abort();
    };
  }, [controller]);

  const stopOutputMessage = useCallback(() => {
    setController((pre) => {
      pre.abort();
      return new AbortController();
    });
  }, []);

  const handleConversationCardClick = useCallback(
    (conversationId: string, isNew: boolean) => {
      setConversationBoth(conversationId, isNew ? 'true' : '');
      stopOutputMessage();
    },
    [setConversationBoth, stopOutputMessage],
  );

  return { controller, handleConversationCardClick, stopOutputMessage };
}
