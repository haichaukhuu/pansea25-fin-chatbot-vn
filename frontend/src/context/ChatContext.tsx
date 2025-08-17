import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Chat, Message, FileItem } from '../types';
import { apiService, type ChatMessage } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

interface ChatContextType {
  chats: Chat[];
  currentChat: Chat | null;
  files: FileItem[];
  isStreaming: boolean;
  streamingMessage: Message | null;
  createNewChat: () => string;
  selectChat: (chatId: string) => void;
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
  stopGeneration: () => void;
  searchChats: (query: string) => Chat[];
  uploadFile: (file: File) => Promise<void>;
  deleteChat: (chatId: string) => void;
  initializeForNewUser: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Demo chat with MOCK_DATA content
const DEMO_CHAT: Chat = {
  id: 'demo-chat-viet',
  title: 'Demo Chat Viet',
  createdAt: new Date(2025, 0, 15, 10, 0),
  updatedAt: new Date(2025, 0, 15, 10, 30),
  messages: [
    {
      id: 'demo-1',
      content: 'Tui muốn nuôi gà, vay được mấy triệu?',
      sender: 'user',
      timestamp: new Date(2025, 0, 15, 10, 0),
      chatId: 'demo-chat-viet'
    },
    {
      id: 'demo-2',
      content: `Chào bạn, rất vui được tư vấn cho bạn về việc vay vốn nuôi gà!

Việc vay được bao nhiêu tiền phụ thuộc vào nhiều yếu tố lắm bạn ơi. Để mình hỏi kỹ hơn một chút nhé:

* Bạn định nuôi bao nhiêu gà? (Ví dụ: 100 con, 500 con, 1000 con...)
* Bạn có đất đai, chuồng trại sẵn chưa? Nếu chưa thì cần tính thêm chi phí xây dựng.
* Bạn ở tỉnh nào? Mỗi tỉnh sẽ có các chính sách hỗ trợ vay vốn khác nhau.
* Bạn có giấy tờ gì để thế chấp không? (Ví dụ: đất đai, tài sản khác...)

Thông thường, các chương trình vay vốn nông nghiệp sẽ cho vay từ **vài triệu đến vài chục triệu đồng**. Tuy nhiên, số tiền cụ thể bạn có thể vay được sẽ dựa trên các yếu tố mình vừa hỏi.`,
      sender: 'bot',
      timestamp: new Date(2025, 0, 15, 10, 1),
      chatId: 'demo-chat-viet'
    },
    {
      id: 'demo-3',
      content: 'Nuôi khoảng 50 con thôi, có 2 công rưỡi đất vườn, ở An Giang, giấy tờ đất có được không?',
      sender: 'user',
      timestamp: new Date(2025, 0, 15, 10, 5),
      chatId: 'demo-chat-viet'
    },
    {
      id: 'demo-4',
      content: `Rất vui được tư vấn tài chính cho bạn về việc nuôi gà. 50 con gà là một khởi đầu tốt, và có 25 héc ta đất là một lợi thế lớn rồi đó ạ. Để tính toán được số tiền bạn có thể vay được, mình cần xem xét kỹ hơn một chút nhé.

### 1. Ước tính chi phí ban đầu:

* **Mua gà con:** Khoảng 30.000 - 50.000 đồng/con, vậy 50 con sẽ tốn khoảng *1.500.000 - 2.500.000 đồng*.
* **Xây chuồng trại:** Tùy vào vật liệu và kiểu chuồng, có thể dao động từ *5.000.000 - 15.000.000 đồng*. Bạn có thể tận dụng một phần đất và vật liệu sẵn có để giảm chi phí.
* **Thức ăn:** Gà cần thức ăn liên tục, ước tính khoảng *3.000.000 - 5.000.000 đồng* cho giai đoạn đầu (khoảng 2-3 tháng).
* **Vắc-xin, thuốc thú y:** Khoảng *500.000 - 1.000.000 đồng*.
* **Chi phí khác:** Đồ uống, máng ăn, dụng cụ vệ sinh... khoảng *500.000 - 1.000.000 đồng*.

👉 **Tổng cộng chi phí ban đầu ước tính:** *Khoảng 10.500.000 - 24.500.000 đồng.*

---

### 2. Các chương trình vay nông nghiệp ở An Giang:

Ở An Giang, bạn có thể tham khảo các chương trình vay sau:

* **Ngân hàng Chính sách Xã hội (NHCSXH):**
  Đây là lựa chọn phổ biến cho nông dân, lãi suất ưu đãi, thủ tục đơn giản. Hiện tại có các gói vay:

  * *Vay hộ nghèo:* Nếu bạn thuộc hộ nghèo, có thể vay tối đa **100 triệu đồng**.
  * *Vay sản xuất kinh doanh:* Cho vay các hộ nông dân có nhu cầu phát triển sản xuất, tối đa **50 triệu đồng**.

* **Ngân hàng Nông nghiệp và Phát triển Nông thôn (Agribank):**
  Có nhiều gói vay dành cho nông dân, lãi suất cạnh tranh.

* **Ngân hàng Thương mại Cổ phần (BIDV, Vietcombank...):**
  Cũng có các gói vay nông nghiệp, nhưng thủ tục có thể phức tạp hơn.

💡 Với 25 héc ta đất và giấy tờ đầy đủ, bạn có thể vay được **từ 20 triệu đến 50 triệu đồng**, tùy thuộc vào chính sách của từng ngân hàng và khả năng chứng minh thu nhập.

---

### 3. Thủ tục vay vốn:

1. **Chuẩn bị hồ sơ:** Giấy tờ tùy thân, giấy tờ đất, kế hoạch nuôi gà chi tiết (bao gồm chi phí, doanh thu dự kiến, thời gian hoàn vốn), giấy tờ chứng minh thu nhập (nếu có).
2. **Đến ngân hàng:** Liên hệ với các ngân hàng trên để được tư vấn cụ thể về thủ tục và lãi suất.
3. **Xét duyệt:** Ngân hàng sẽ xét duyệt hồ sơ của bạn.
4. **Giải ngân:** Nếu được duyệt, ngân hàng sẽ giải ngân vốn cho bạn.

---

### 4. Lưu ý quan trọng:

* **Lãi suất:** So sánh lãi suất của các ngân hàng khác nhau để chọn được gói vay phù hợp.
* **Thời gian vay:** Chọn thời gian vay phù hợp với khả năng trả nợ của bạn.
* **Đọc kỹ hợp đồng:** Đọc kỹ các điều khoản trong hợp đồng vay trước khi ký.
* **Cẩn thận với các đối tượng lừa đảo:** Đừng tin vào những lời mời vay vốn quá dễ dàng, lãi suất quá thấp, hoặc yêu cầu bạn đóng tiền trước.

---

✅ **Lời khuyên:**
Bạn nên bắt đầu với quy mô nhỏ (50 con) để tích lũy kinh nghiệm trước khi mở rộng. Nên tìm hiểu kỹ về kỹ thuật nuôi gà, phòng bệnh cho gà để đảm bảo hiệu quả và nên tìm đầu ra ổn định cho sản phẩm gà của mình.

Nếu bạn cần thêm thông tin chi tiết về các chương trình vay hoặc có bất kỳ câu hỏi nào khác, đừng ngần ngại hỏi tôi nhé! Tôi luôn sẵn lòng hỗ trợ bạn.

**Chúc bạn thành công với mô hình nuôi gà của mình!**`,
      sender: 'bot',
      timestamp: new Date(2025, 0, 15, 10, 6),
      chatId: 'demo-chat-viet'
    }
  ]
};

// Demo data
// const DEMO_CHATS: Chat[] = [
//   {
//     id: '1',
//     title: 'Demo Chatbot Tài chính',
//     createdAt: new Date(2025, 6, 30),
//     updatedAt: new Date(2025, 6, 30),
//     messages: [
//       {
//         id: '1',
//         content: 'Xin chào! Bạn có thể giúp tôi lập kế hoạch tài chính không?',
//         sender: 'user',
//         timestamp: new Date(2025, 6, 30, 10, 0),
//         chatId: '1'
//       },
//       {
//         id: '2',
//         content: 'Tất nhiên! Tôi rất vui được giúp bạn lập kế hoạch tài chính. Hãy bắt đầu với mục tiêu tài chính của bạn. Bạn muốn đạt được điều gì?',
//         sender: 'bot',
//         timestamp: new Date(2025, 6, 30, 10, 1),
//         chatId: '1'
//       }
//     ]
//   },
//   {
//     id: '2',
//     title: 'Trợ giúp Chatbot Tài chính',
//     createdAt: new Date(2025, 6, 29),
//     updatedAt: new Date(2025, 6, 29),
//     messages: [
//       {
//         id: '3',
//         content: 'Những chiến lược đầu tư nào tốt cho người mới bắt đầu?',
//         sender: 'user',
//         timestamp: new Date(2025, 6, 29, 14, 30),
//         chatId: '2'
//       },
//       {
//         id: '4',
//         content: 'Đối với người mới bắt đầu, tôi khuyên bạn nên bắt đầu với quỹ chỉ số đa dạng hóa, thiết lập quỹ khẩn cấp và hiểu rõ mức độ chấp nhận rủi ro của mình. Bạn có muốn tôi giải thích chi tiết về bất kỳ điều nào trong số này không?',
//         sender: 'bot',
//         timestamp: new Date(2025, 6, 29, 14, 31),
//         chatId: '2'
//       }
//     ]
//   }
// ];

// const DEMO_FILES: FileItem[] = [
//   {
//     id: '1',
//     name: 'Kế_hoạch_Tài_chính_2025.pdf',
//     type: 'application/pdf',
//     size: 1024000,
//     url: '/demo/financial_plan.pdf',
//     createdAt: new Date(2025, 6, 30),
//     chatId: '1'
//   },
//   {
//     id: '2',
//     name: 'Danh_mục_Đầu_tư.xlsx',
//     type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
//     size: 512000,
//     url: '/demo/portfolio.xlsx',
//     createdAt: new Date(2025, 6, 29),
//     chatId: '2'
//   }
// ];

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const { t } = useLanguage();

  const createNewChat = (): string => {
    const newChat: Chat = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'Cuộc trò chuyện mới',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChat(newChat);
    return newChat.id;
  };

  const selectChat = (chatId: string) => {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setCurrentChat(chat);
    }
  };

  const sendMessage = async (content: string, useStreaming: boolean = true) => {
    if (!currentChat) return;

    const userMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      content,
      sender: 'user',
      timestamp: new Date(),
      chatId: currentChat.id
    };

    // Add user message immediately
    const chatWithUserMessage = {
      ...currentChat,
      messages: [...currentChat.messages, userMessage],
      updatedAt: new Date(),
      title: currentChat.messages.length === 0 ? content.slice(0, 30) + '...' : currentChat.title
    };

    setChats(prev => prev.map(chat => 
      chat.id === currentChat.id ? chatWithUserMessage : chat
    ));
    setCurrentChat(chatWithUserMessage);

    try {
      // Prepare chat history for API call
      const chatHistory: ChatMessage[] = chatWithUserMessage.messages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'bot',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }));

      const request = {
        message: content,
        chat_history: chatHistory.slice(0, -1), // Exclude the current message we just sent
        user_profile: {} // You can add user profile data here if available
      };

      if (useStreaming) {
        // For demo purposes, we'll create a mock streaming response if the backend is not available
        setIsStreaming(true);
        
        // Create initial streaming message
        const streamingMsg: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: '',
          sender: 'bot',
          timestamp: new Date(),
          chatId: currentChat.id,
          isStreaming: true,
          isComplete: false
        };

        setStreamingMessage(streamingMsg);

        // Add streaming message to chat
        const chatWithStreamingMessage = {
          ...chatWithUserMessage,
          messages: [...chatWithUserMessage.messages, streamingMsg],
          updatedAt: new Date()
        };

        setChats(prev => prev.map(chat => 
          chat.id === currentChat.id ? chatWithStreamingMessage : chat
        ));
        setCurrentChat(chatWithStreamingMessage);

        try {
          await apiService.sendStreamingMessage(
            request,
            // On chunk received
            (chunk: string) => {
              setStreamingMessage(prevMsg => {
                if (!prevMsg) return null;
                const updatedMsg = {
                  ...prevMsg,
                  content: prevMsg.content + chunk
                };
                
                // Update the message in the chat
                setChats(prev => prev.map(chat => 
                  chat.id === currentChat.id 
                    ? {
                        ...chat,
                        messages: chat.messages.map(msg => 
                          msg.id === updatedMsg.id ? updatedMsg : msg
                        )
                      }
                    : chat
                ));
                setCurrentChat(prev => prev ? {
                  ...prev,
                  messages: prev.messages.map(msg => 
                    msg.id === updatedMsg.id ? updatedMsg : msg
                  )
                } : null);

                return updatedMsg;
              });
            },
            // On complete
            () => {
              setIsStreaming(false);
              setStreamingMessage(prevMsg => {
                if (!prevMsg) return null;
                const completedMsg = {
                  ...prevMsg,
                  isStreaming: false,
                  isComplete: true
                };

                // Update the final message in the chat
                setChats(prev => prev.map(chat => 
                  chat.id === currentChat.id 
                    ? {
                        ...chat,
                        messages: chat.messages.map(msg => 
                          msg.id === completedMsg.id ? completedMsg : msg
                        )
                      }
                    : chat
                ));
                setCurrentChat(prev => prev ? {
                  ...prev,
                  messages: prev.messages.map(msg => 
                    msg.id === completedMsg.id ? completedMsg : msg
                  )
                } : null);

                return null; // Clear streaming message
              });
            },
            // On error
            (error: Error) => {
              console.error('Streaming error:', error);
              setIsStreaming(false);
              setStreamingMessage(null);
              
              // Add error message
              const errorMessage: Message = {
                id: Math.random().toString(36).substr(2, 9),
                content: t('api.streaming_error', { error: error.message }),
                sender: 'bot',
                timestamp: new Date(),
                chatId: currentChat.id
              };

              const errorChat = {
                ...chatWithUserMessage,
                messages: [...chatWithUserMessage.messages, errorMessage],
                updatedAt: new Date()
              };

              setChats(prev => prev.map(chat => 
                chat.id === currentChat.id ? errorChat : chat
              ));
              setCurrentChat(errorChat);
            }
          );
        } catch (apiError) {
          // If API call fails, create a mock streaming response for testing
          console.log('API unavailable, creating mock streaming response for testing');
          
          const mockResponse = t('api.mock_error');
          
          let index = 0;
          const streamInterval = setInterval(() => {
            if (index < mockResponse.length && isStreaming) {
              setStreamingMessage(prevMsg => {
                if (!prevMsg) return null;
                const updatedMsg = {
                  ...prevMsg,
                  content: prevMsg.content + mockResponse[index]
                };
                
                // Update the message in the chat
                setChats(prev => prev.map(chat => 
                  chat.id === currentChat.id 
                    ? {
                        ...chat,
                        messages: chat.messages.map(msg => 
                          msg.id === updatedMsg.id ? updatedMsg : msg
                        )
                      }
                    : chat
                ));
                setCurrentChat(prev => prev ? {
                  ...prev,
                  messages: prev.messages.map(msg => 
                    msg.id === updatedMsg.id ? updatedMsg : msg
                  )
                } : null);

                return updatedMsg;
              });
              index++;
            } else {
              clearInterval(streamInterval);
              setIsStreaming(false);
              setStreamingMessage(prevMsg => {
                if (!prevMsg) return null;
                const completedMsg = {
                  ...prevMsg,
                  isStreaming: false,
                  isComplete: true
                };

                // Update the final message in the chat
                setChats(prev => prev.map(chat => 
                  chat.id === currentChat.id 
                    ? {
                        ...chat,
                        messages: chat.messages.map(msg => 
                          msg.id === completedMsg.id ? completedMsg : msg
                        )
                      }
                    : chat
                ));
                setCurrentChat(prev => prev ? {
                  ...prev,
                  messages: prev.messages.map(msg => 
                    msg.id === completedMsg.id ? completedMsg : msg
                  )
                } : null);

                return null; // Clear streaming message
              });
            }
          }, 50); // Stream one character every 50ms for demo
        }
      } else {
        // Use non-streaming approach (fallback)
        const response = await apiService.sendMessage(request);

        // Create bot response message
        const botMessage: Message = {
          id: Math.random().toString(36).substr(2, 9),
          content: response.response,
          sender: 'bot',
          timestamp: new Date(),
          chatId: currentChat.id,
          isComplete: true
        };

        // Update chat with bot response
        const updatedChat = {
          ...chatWithUserMessage,
          messages: [...chatWithUserMessage.messages, botMessage],
          updatedAt: new Date()
        };

        setChats(prev => prev.map(chat => 
          chat.id === currentChat.id ? updatedChat : chat
        ));
        setCurrentChat(updatedChat);
      }

    } catch (error) {
      console.error('Failed to get AI response:', error);
      setIsStreaming(false);
      setStreamingMessage(null);
      
      // Fallback to error message if API fails
      const errorMessage: Message = {
        id: Math.random().toString(36).substr(2, 9),
        content: t('api.connection_error'),
        sender: 'bot',
        timestamp: new Date(),
        chatId: currentChat.id
      };

      const errorChat = {
        ...chatWithUserMessage,
        messages: [...chatWithUserMessage.messages, errorMessage],
        updatedAt: new Date()
      };

      setChats(prev => prev.map(chat => 
        chat.id === currentChat.id ? errorChat : chat
      ));
      setCurrentChat(errorChat);
    }
  };

  const searchChats = (query: string): Chat[] => {
    if (!query.trim()) return chats;
    
    return chats.filter(chat => 
      chat.title.toLowerCase().includes(query.toLowerCase()) ||
      chat.messages.some(message => 
        message.content.toLowerCase().includes(query.toLowerCase())
      )
    );
  };

  const uploadFile = async (file: File): Promise<void> => {
    const newFile: FileItem = {
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.type,
      size: file.size,
      url: URL.createObjectURL(file),
      createdAt: new Date(),
      chatId: currentChat?.id || ''
    };
    setFiles(prev => [newFile, ...prev]);
  };

  const deleteChat = (chatId: string) => {
    // Prevent deletion of demo chat
    if (chatId === 'demo-chat-viet') {
      return;
    }
    
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChat?.id === chatId) {
      setCurrentChat(chats.length > 1 ? chats[0] : null);
    }
  };

  const stopGeneration = () => {
    if (isStreaming) {
      // Stop the API streaming request
      apiService.stopStreaming();
      
      // Reset streaming state
      setIsStreaming(false);
      
      // If there's a streaming message, mark it as complete
      if (streamingMessage) {
        const completedMsg = {
          ...streamingMessage,
          isStreaming: false,
          isComplete: true
        };

        // Update the message in the chat
        setChats(prev => prev.map(chat => 
          chat.id === currentChat?.id 
            ? {
                ...chat,
                messages: chat.messages.map(msg => 
                  msg.id === completedMsg.id ? completedMsg : msg
                )
              }
            : chat
        ));
        setCurrentChat(prev => prev ? {
          ...prev,
          messages: prev.messages.map(msg => 
            msg.id === completedMsg.id ? completedMsg : msg
          )
        } : null);

        setStreamingMessage(null);
      }
    }
  };

  const initializeForNewUser = () => {
    // Create demo chat and a new empty chat for the user when they sign in
    const newChat: Chat = {
      id: Math.random().toString(36).substr(2, 9),
      title: 'Cuộc trò chuyện mới',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    setChats([newChat, DEMO_CHAT]);
    setCurrentChat(newChat); // Set new chat as current by default
    setFiles([]);
  };

  return (
    <ChatContext.Provider value={{
      chats,
      currentChat,
      files,
      isStreaming,
      streamingMessage,
      createNewChat,
      selectChat,
      sendMessage,
      stopGeneration,
      searchChats,
      uploadFile,
      deleteChat,
      initializeForNewUser
    }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
