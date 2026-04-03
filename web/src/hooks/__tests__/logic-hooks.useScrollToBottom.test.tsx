jest.mock('eventsource-parser/stream', () => ({}));

import { act, renderHook } from '@testing-library/react';
import { useScrollToBottom } from '../logic-hooks';

function createMockContainer({ atBottom = true } = {}) {
  const scrollTop = atBottom ? 100 : 0;
  const clientHeight = 100;
  const scrollHeight = 200;
  const listeners = {};
  return {
    current: {
      scrollTop,
      clientHeight,
      scrollHeight,
      addEventListener: jest.fn((event, cb) => {
        listeners[event] = cb;
      }),
      removeEventListener: jest.fn(),
    },
    listeners,
  } as any;
}

// Helper to flush all timers and microtasks
async function flushAll() {
  jest.runAllTimers();
  // Flush microtasks
  await Promise.resolve();
  // Sometimes, effects queue more timers, so run again
  jest.runAllTimers();
  await Promise.resolve();
}

describe('useScrollToBottom', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it('should set isAtBottom true when user is at bottom', () => {
    const containerRef = createMockContainer({ atBottom: true });
    const { result } = renderHook(() => useScrollToBottom([], containerRef));
    expect(result.current.isAtBottom).toBe(true);
  });

  it('should set isAtBottom false when user is not at bottom', () => {
    const containerRef = createMockContainer({ atBottom: false });
    const { result } = renderHook(() => useScrollToBottom([], containerRef));
    expect(result.current.isAtBottom).toBe(false);
  });

  it('should scroll to bottom when isAtBottom is true and messages change', async () => {
    const containerRef = createMockContainer({ atBottom: true });
    const mockScroll = jest.fn();

    function useTestScrollToBottom(messages: any, containerRef: any) {
      const hook = useScrollToBottom(messages, containerRef);
      hook.scrollRef.current = { scrollIntoView: mockScroll } as any;
      return hook;
    }

    const { rerender } = renderHook(
      ({ messages }) => useTestScrollToBottom(messages, containerRef),
      { initialProps: { messages: [] } },
    );

    rerender({ messages: ['msg1'] });
    await flushAll();

    expect(mockScroll).toHaveBeenCalled();
  });

  it('should NOT scroll to bottom when isAtBottom is false and messages change', async () => {
    const containerRef = createMockContainer({ atBottom: false });
    const mockScroll = jest.fn();

    function useTestScrollToBottom(messages: any, containerRef: any) {
      const hook = useScrollToBottom(messages, containerRef);
      hook.scrollRef.current = { scrollIntoView: mockScroll } as any;
      return hook;
    }

    const { result, rerender } = renderHook(
      ({ messages }) => useTestScrollToBottom(messages, containerRef),
      { initialProps: { messages: [] } },
    );

    // Simulate user scrolls up before messages change
    await act(async () => {
      containerRef.current.scrollTop = 0;
      containerRef.current.addEventListener.mock.calls[0][1]();
      await flushAll();
      // Advance fake timers by 10ms instead of real setTimeout
      jest.advanceTimersByTime(10);
    });

    rerender({ messages: ['msg1'] });
    await flushAll();

    expect(mockScroll).not.toHaveBeenCalled();

    // Optionally, flush again after the assertion to see if it gets called late
    await flushAll();
  });

  it('should indicate button should appear when user is not at bottom', () => {
    const containerRef = createMockContainer({ atBottom: false });
    const { result } = renderHook(() => useScrollToBottom([], containerRef));
    // The button should appear in the UI when isAtBottom is false
    expect(result.current.isAtBottom).toBe(false);
  });

  it('should handle multiple rapid message additions', async () => {
    const containerRef = createMockContainer({ atBottom: true });
    const mockScroll = jest.fn();

    function useTestScrollToBottom(messages: any, containerRef: any) {
      const hook = useScrollToBottom(messages, containerRef);
      hook.scrollRef.current = { scrollIntoView: mockScroll } as any;
      return hook;
    }

    const { rerender } = renderHook(
      ({ messages }) => useTestScrollToBottom(messages, containerRef),
      { initialProps: { messages: [] } },
    );

    // Simulate multiple rapid messages
    rerender({ messages: ['msg1'] });
    rerender({ messages: ['msg1', 'msg2'] });
    rerender({ messages: ['msg1', 'msg2', 'msg3'] });
    await flushAll();

    // Should have been called for the initial change, not for each subsequent change
    // when already at bottom and scroll already triggered
    expect(mockScroll).toHaveBeenCalled();
    // More specifically, it should be called at least once
    expect(mockScroll.mock.calls.length).toBeGreaterThanOrEqual(1);
  });

  it('should handle messages becoming empty', async () => {
    const containerRef = createMockContainer({ atBottom: true });
    const mockScroll = jest.fn();

    function useTestScrollToBottom(messages: any, containerRef: any) {
      const hook = useScrollToBottom(messages, containerRef);
      hook.scrollRef.current = { scrollIntoView: mockScroll } as any;
      return hook;
    }

    const { rerender } = renderHook(
      ({ messages }) => useTestScrollToBottom(messages, containerRef),
      { initialProps: { messages: ['msg1', 'msg2'] } },
    );

    rerender({ messages: [] });
    await flushAll();

    // Should handle empty messages array gracefully
    expect(mockScroll).toHaveBeenCalled();
  });

  it('should handle container ref with undefined scroll properties', () => {
    const containerRef = {
      current: {
        scrollTop: undefined,
        clientHeight: undefined,
        scrollHeight: undefined,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      },
    } as any;

    // Should not throw an error
    expect(() => {
      const { result } = renderHook(() => useScrollToBottom([], containerRef));
      // Basic check that the hook returned something
      expect(result.current).toBeDefined();
      expect(result.current.isAtBottom).toBeDefined();
    }).not.toThrow();
  });
});

const originalRAF = global.requestAnimationFrame;
beforeAll(() => {
  global.requestAnimationFrame = (cb) => setTimeout(cb, 0);
});
afterAll(() => {
  global.requestAnimationFrame = originalRAF;
});
