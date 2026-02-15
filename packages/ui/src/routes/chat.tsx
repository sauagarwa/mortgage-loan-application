import { createFileRoute } from '@tanstack/react-router';
import { ChatContainer } from '../components/chat/chat-container';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/chat' as any)({
  component: ChatPage,
});

function ChatPage() {
  return <ChatContainer />;
}
