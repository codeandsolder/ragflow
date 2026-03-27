import { useCallback, useEffect, useRef } from 'react';

export function useHandleClickConversationCard() {
  const controllerRef = useRef(new AbortController());
  const { setConversationBoth } = useChatUrlParams();

  useEffect(() => {
    return () => {
      controllerRef.current.abort();
    };
  }, []);

  const stopOutputMessage = useCallback(() => {
    controllerRef.current.abort();
    controllerRef.current = new AbortController();
  }, []);

  const handleConversationCardClick = useCallback(
    (conversationId: string, isNew: boolean) => {
      setConversationBoth(conversationId, isNew ? 'true' : '');
      stopOutputMessage();
    },
    [setConversationBoth, stopOutputMessage],
  );

  return {
    controller: controllerRef,
    handleConversationCardClick,
    stopOutputMessage,
  };
}
