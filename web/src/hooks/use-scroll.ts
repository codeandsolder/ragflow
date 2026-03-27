import { useCallback, useEffect, useRef, useState } from 'react';

export const useScrollToBottom = (
  messages?: unknown,
  containerRef?: React.RefObject<HTMLDivElement>,
) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const isAtBottomRef = useRef(true);
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    isAtBottomRef.current = isAtBottom;
  }, [isAtBottom]);

  const checkIfUserAtBottom = useCallback(() => {
    if (!containerRef?.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    return Math.abs(scrollTop + clientHeight - scrollHeight) < 25;
  }, [containerRef]);

  useEffect(() => {
    if (!containerRef?.current) return;
    const container = containerRef.current;

    const handleScroll = () => {
      if (scrollTimeoutRef.current) {
        return;
      }
      scrollTimeoutRef.current = setTimeout(() => {
        scrollTimeoutRef.current = null;
        setIsAtBottom(checkIfUserAtBottom());
      }, 16);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [containerRef, checkIfUserAtBottom]);

  const scrollToBottom = useCallback(() => {
    if (containerRef?.current) {
      const container = containerRef.current;
      container.scrollTo({
        top: container.scrollHeight - container.clientHeight,
        behavior: 'auto',
      });
    }
  }, [containerRef]);

  useEffect(() => {
    if (!messages) return;
    if (!containerRef?.current) return;
    requestAnimationFrame(() => {
      if (isAtBottomRef.current) {
        scrollToBottom();
      }
    });
  }, [messages, containerRef, scrollToBottom]);

  return { scrollRef: ref, isAtBottom, scrollToBottom };
};
