import message from '@/components/ui/message';
import { Authorization } from '@/constants/authorization';
import { MessageType } from '@/constants/chat';
import { ResponseType } from '@/interfaces/database/base';
import {
  IAnswer,
  IClientConversation,
  IMessage,
  Message,
} from '@/interfaces/database/chat';
import api from '@/utils/api';
import { getAuthorization } from '@/utils/authorization-util';
import { buildMessageUuid } from '@/utils/chat';
import { EventSourceParserStream } from 'eventsource-parser/stream';
import { has, isEmpty, omit } from 'lodash';
import {
  ChangeEventHandler,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { v4 as uuid } from 'uuid';
import { useScrollToBottom } from './use-scroll';

function useSetDoneRecord() {
  const [doneRecord, setDoneRecord] = useState<Record<string, boolean>>({});

  const clearDoneRecord = useCallback(() => {
    setDoneRecord({});
  }, []);

  const setDoneRecordById = useCallback((id: string, val: boolean) => {
    setDoneRecord((prev) => ({ ...prev, [id]: val }));
  }, []);

  const allDone = useMemo(() => {
    return Object.values(doneRecord).every((val) => val);
  }, [doneRecord]);

  useEffect(() => {
    if (!isEmpty(doneRecord) && allDone) {
      clearDoneRecord();
    }
  }, [allDone, clearDoneRecord, doneRecord]);

  return {
    doneRecord,
    setDoneRecord,
    setDoneRecordById,
    clearDoneRecord,
    allDone,
  };
}

export const useSendMessageWithSse = (
  url: string = api.completeConversation,
) => {
  const [answer, setAnswer] = useState<IAnswer>({} as IAnswer);
  const [done, setDone] = useState(true);
  const { doneRecord, clearDoneRecord, setDoneRecordById, allDone } =
    useSetDoneRecord();
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const sseRef = useRef<AbortController>();

  const initializeSseRef = useCallback(() => {
    sseRef.current = new AbortController();
  }, []);

  useEffect(() => {
    return () => {
      sseRef.current?.abort();
      if (timer.current) {
        clearTimeout(timer.current);
      }
    };
  }, []);

  const resetAnswer = useCallback(() => {
    if (timer.current) {
      clearTimeout(timer.current);
    }
    timer.current = setTimeout(() => {
      setAnswer({} as IAnswer);
      clearTimeout(timer.current);
    }, 1000);
  }, []);

  const setDoneValue = useCallback(
    (body: any, value: boolean) => {
      if (has(body, 'chatBoxId')) {
        setDoneRecordById(body.chatBoxId, value);
      } else {
        setDone(value);
      }
    },
    [setDoneRecordById],
  );

  const send = useCallback(
    async (
      body: any,
      controller?: AbortController,
    ): Promise<{ response: Response; data: ResponseType } | undefined> => {
      initializeSseRef();
      try {
        setDoneValue(body, false);
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            [Authorization]: getAuthorization(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(omit(body, 'chatBoxId')),
          signal: controller?.signal || sseRef.current?.signal,
        });

        const res = response.clone().json();

        const reader = response?.body
          ?.pipeThrough(new TextDecoderStream())
          .pipeThrough(new EventSourceParserStream())
          .getReader();

        while (true) {
          try {
            const x = await reader?.read();
            if (x) {
              const { done, value } = x;
              if (done) {
                resetAnswer();
                break;
              }
              try {
                const val = JSON.parse(value?.data || '');
                const d = val?.data;
                if (typeof d !== 'boolean') {
                  setAnswer((prev) => {
                    const prevAnswer = prev.answer || '';
                    const currentAnswer = d.answer || '';

                    let newAnswer: string;
                    if (prevAnswer && currentAnswer.startsWith(prevAnswer)) {
                      newAnswer = currentAnswer;
                    } else {
                      newAnswer = prevAnswer + currentAnswer;
                    }

                    if (d.start_to_think === true) {
                      newAnswer = newAnswer + '<think>';
                    }

                    if (d.end_to_think === true) {
                      newAnswer = newAnswer + '</think>';
                    }

                    return {
                      ...d,
                      answer: newAnswer,
                      conversationId: body?.conversation_id,
                      chatBoxId: body.chatBoxId,
                    };
                  });
                }
              } catch (e) {
                // Swallow parse errors silently
              }
            }
          } catch (e) {
            if (e instanceof DOMException && e.name === 'AbortError') {
              break;
            }
          }
        }
        setDoneValue(body, true);
        resetAnswer();
        return { data: await res, response };
      } catch (e) {
        setDoneValue(body, true);
        resetAnswer();
        // Swallow fetch errors silently
      }
    },
    [initializeSseRef, setDoneValue, url, resetAnswer],
  );

  const stopOutputMessage = useCallback(() => {
    sseRef.current?.abort();
  }, []);

  return {
    send,
    answer,
    done,
    doneRecord,
    allDone,
    setDone,
    resetAnswer,
    stopOutputMessage,
    clearDoneRecord,
  };
};

export const useSpeechWithSse = (url: string = api.tts) => {
  const sseRef = useRef<AbortController>();

  useEffect(() => {
    return () => {
      sseRef.current?.abort();
    };
  }, []);

  const read = useCallback(
    async (body: any) => {
      sseRef.current = new AbortController();
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          [Authorization]: getAuthorization(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: sseRef.current.signal,
      });
      try {
        const res = await response.clone().json();
        if (res?.code !== 0) {
          message.error(res?.message);
        }
      } catch (error) {
        // Swallow errors silently
      }
      return response;
    },
    [url],
  );

  return { read };
};

export const useHandleMessageInputChange = () => {
  const [value, setValue] = useState('');

  const handleInputChange: ChangeEventHandler<HTMLTextAreaElement> = (e) => {
    const value = e.target.value;
    const nextValue = value.replaceAll('\\n', '\n').replaceAll('\\t', '\t');
    setValue(nextValue);
  };

  return {
    handleInputChange,
    value,
    setValue,
  };
};

export const useSelectDerivedMessages = () => {
  const [derivedMessages, setDerivedMessages] = useState<IMessage[]>([]);

  const messageContainerRef = useRef<HTMLDivElement>(null);

  const { scrollRef, scrollToBottom } = useScrollToBottom(
    derivedMessages,
    messageContainerRef,
  );

  const addNewestQuestion = useCallback(
    (message: IMessage, answer: string = '') => {
      setDerivedMessages((pre) => {
        return [
          ...pre,
          {
            ...message,
            id: buildMessageUuid(message),
          },
          {
            role: MessageType.Assistant,
            content: answer,
            conversationId: message.conversationId,
            id: buildMessageUuid({ ...message, role: MessageType.Assistant }),
          },
        ];
      });
    },
    [],
  );

  const addNewestOneQuestion = useCallback((message: Message) => {
    setDerivedMessages((pre) => {
      return [
        ...pre,
        {
          ...message,
          id: buildMessageUuid(message),
        },
      ];
    });
  }, []);

  const addNewestAnswer = useCallback((answer: IAnswer) => {
    setDerivedMessages((pre) => {
      return [
        ...(pre?.slice(0, -1) ?? []),
        {
          role: MessageType.Assistant,
          content: answer.answer,
          reference: answer.reference,
          id: buildMessageUuid({
            id: answer.id,
            role: MessageType.Assistant,
          }),
          prompt: answer.prompt,
          audio_binary: answer.audio_binary,
          ...omit(answer, 'reference'),
        },
      ];
    });
  }, []);

  const addNewestOneAnswer = useCallback((answer: IAnswer) => {
    setDerivedMessages((pre) => {
      const idx = pre.findIndex((x) => x.id === answer.id);

      if (idx !== -1) {
        return pre.map((x) => {
          if (x.id === answer.id) {
            return { ...x, ...answer, content: answer.answer };
          }
          return x;
        });
      }

      return [
        ...(pre ?? []),
        {
          role: MessageType.Assistant,
          content: answer.answer,
          reference: answer.reference,
          id: buildMessageUuid({
            id: answer.id,
            role: MessageType.Assistant,
          }),
          prompt: answer.prompt,
          audio_binary: answer.audio_binary,
          ...omit(answer, 'reference'),
        },
      ];
    });
  }, []);

  const addPrologue = useCallback((prologue: string) => {
    setDerivedMessages((pre) => {
      if (pre.length > 0) {
        return [
          {
            ...pre[0],
            content: prologue,
          },
          ...pre.slice(1),
        ];
      }

      return [
        {
          role: MessageType.Assistant,
          content: prologue,
          id: buildMessageUuid({
            role: MessageType.Assistant,
          }),
        },
      ];
    });
  }, []);

  const removeLatestMessage = useCallback(() => {
    setDerivedMessages((pre) => {
      const nextMessages = pre?.slice(0, -2) ?? [];
      return nextMessages;
    });
  }, []);

  const removeMessageById = useCallback(
    (messageId: string) => {
      setDerivedMessages((pre) => {
        const nextMessages = pre?.filter((x) => x.id !== messageId) ?? [];
        return nextMessages;
      });
    },
    [setDerivedMessages],
  );

  const removeMessagesAfterCurrentMessage = useCallback(
    (messageId: string) => {
      setDerivedMessages((pre) => {
        const index = pre.findIndex((x) => x.id === messageId);
        if (index !== -1) {
          let nextMessages = pre.slice(0, index + 2) ?? [];
          const latestMessage = nextMessages.at(-1);
          nextMessages = latestMessage
            ? [
                ...nextMessages.slice(0, -1),
                {
                  ...latestMessage,
                  content: '',
                  reference: undefined,
                  prompt: undefined,
                },
              ]
            : nextMessages;
          return nextMessages;
        }
        return pre;
      });
    },
    [setDerivedMessages],
  );

  const removeAllMessages = useCallback(() => {
    setDerivedMessages([]);
  }, [setDerivedMessages]);

  const removeAllMessagesExceptFirst = useCallback(() => {
    setDerivedMessages((list) => {
      if (list.length <= 1) {
        return list;
      }
      return list.slice(0, 1);
    });
  }, [setDerivedMessages]);

  return {
    scrollRef,
    messageContainerRef,
    derivedMessages,
    setDerivedMessages,
    addNewestQuestion,
    addNewestAnswer,
    removeLatestMessage,
    removeMessageById,
    addNewestOneQuestion,
    addNewestOneAnswer,
    removeMessagesAfterCurrentMessage,
    removeAllMessages,
    scrollToBottom,
    removeAllMessagesExceptFirst,
    addPrologue,
  };
};

export interface IRemoveMessageById {
  removeMessageById(messageId: string): void;
}

export const useRemoveMessagesAfterCurrentMessage = (
  setCurrentConversation: (
    callback: (state: IClientConversation) => IClientConversation,
  ) => void,
) => {
  const removeMessagesAfterCurrentMessage = useCallback(
    (messageId: string) => {
      setCurrentConversation((pre) => {
        const index = pre.message?.findIndex((x) => x.id === messageId);
        if (index !== -1) {
          let nextMessages = pre.message?.slice(0, index + 2) ?? [];
          const latestMessage = nextMessages.at(-1);
          nextMessages = latestMessage
            ? [
                ...nextMessages.slice(0, -1),
                {
                  ...latestMessage,
                  content: '',
                  reference: undefined,
                  prompt: undefined,
                },
              ]
            : nextMessages;
          return {
            ...pre,
            message: nextMessages,
          };
        }
        return pre;
      });
    },
    [setCurrentConversation],
  );

  return { removeMessagesAfterCurrentMessage };
};

export interface IRegenerateMessage {
  regenerateMessage?: (message: Message) => void;
}

export const useRegenerateMessage = ({
  removeMessagesAfterCurrentMessage,
  sendMessage,
  messages,
}: {
  removeMessagesAfterCurrentMessage(messageId: string): void;
  sendMessage({
    message,
  }: {
    message: Message;
    messages?: Message[];
  }): void | Promise<any>;
  messages: Message[];
}) => {
  const regenerateMessage = useCallback(
    async (message: Message) => {
      if (message.id) {
        removeMessagesAfterCurrentMessage(message.id);
        const index = messages.findIndex((x) => x.id === message.id);
        let nextMessages;
        if (index !== -1) {
          nextMessages = messages.slice(0, index);
        }
        sendMessage({
          message: { ...message, id: uuid() },
          messages: nextMessages,
        });
      }
    },
    [removeMessagesAfterCurrentMessage, sendMessage, messages],
  );

  return { regenerateMessage };
};
